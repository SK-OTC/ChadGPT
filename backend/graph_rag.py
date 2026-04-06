"""
Graph RAG module for ChadGPT
Entity-relationship knowledge graph built from Wikipedia data.

Architecture:
  - LangChain WikipediaLoader → fetch Wikipedia (Chad + all 6 neighboring countries)
  - spaCy en_core_web_sm → Named Entity Recognition (GPE/LOC/ORG/NORP entities as nodes)
  - NetworkX → heterogeneous graph:
        nodes: text chunks  (node_type="chunk")
               named entities (node_type="entity")
        edges: sequential adjacency   (within same article)
               chunk ↔ entity mentions  (chunk references entity)
               entity co-occurrence     (two entities in same chunk)
               cross-country relations  (hardcoded geopolitical edges)
  - HuggingFace sentence-transformers → vector embeddings for chunk nodes
  - NumPy cosine similarity → seed chunk selection
  - Entity-bridged expansion → entity-linked multi-hop retrieval
"""

import os
import pickle
import threading
from collections import defaultdict

import networkx as nx
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')
HF_TOKEN = os.environ.get('HF_TOKEN')
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "graph_cache.pkl")
CACHE_VERSION = 3  # bumped from v2 — invalidates old chunk-only caches

# Chad core articles + all bordering countries for cross-country relationship mapping
CHAD_WIKI_PAGES = [
    "Chad",
    "N'Djamena",
    "Lake Chad",
    "Economy of Chad",
    "History of Chad",
    "Zakouma National Park",
    "Ennedi Plateau",
    "Tibesti Mountains",
    "Ounianga Lakes",
    "Demographics of Chad",
    # Neighboring countries
    "Niger",
    "Nigeria",
    "Sudan",
    "Libya",
    "Cameroon",
    "Central African Republic",
    # Regional bodies
    "Lake Chad Basin Commission",
]

# Explicit geopolitical triples — always wired into the graph regardless of NER
CROSS_COUNTRY_RELATIONS: list[tuple[str, str, str]] = [
    ("Chad", "borders", "Niger"),
    ("Chad", "borders", "Nigeria"),
    ("Chad", "borders", "Sudan"),
    ("Chad", "borders", "Libya"),
    ("Chad", "borders", "Cameroon"),
    ("Chad", "borders", "Central African Republic"),
    ("Chad", "shares Lake Chad with", "Niger"),
    ("Chad", "shares Lake Chad with", "Nigeria"),
    ("Chad", "shares Lake Chad with", "Cameroon"),
    ("Chad", "member of", "Lake Chad Basin Commission"),
    ("Niger", "member of", "Lake Chad Basin Commission"),
    ("Nigeria", "member of", "Lake Chad Basin Commission"),
    ("Cameroon", "member of", "Lake Chad Basin Commission"),
    ("Central African Republic", "member of", "Lake Chad Basin Commission"),
]

# spaCy NER label types to keep as entity nodes
RELEVANT_NER_LABELS = {"GPE", "LOC", "ORG", "NORP"}
# Entity must appear in at least this many chunks to become a node
MIN_ENTITY_FREQ = 2


class ChadGraphRAG:
    """
    Entity-relationship Graph RAG over Wikipedia knowledge about Chad and neighbors.

    Usage:
        rag = ChadGraphRAG()
        rag.initialize()
        results = rag.search("cross-border trade between Chad and Nigeria")
    """

    def __init__(self):
        self.embedder = None
        self.nlp = None
        self.graph: nx.Graph = nx.Graph()
        self.chunks: list[str] = []
        self.chunk_metadata: list[dict] = []
        self.embeddings: np.ndarray | None = None
        self._entity_to_node: dict[str, int] = {}
        self._lock = threading.Lock()
        self._initialized = False
        self._init_error: str | None = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_embedder(self):
        if self.embedder is None:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
            print("Graph RAG: Loading HuggingFace embedding model...")
            self.embedder = SentenceTransformer(EMBED_MODEL, token=HF_TOKEN)

    def _load_nlp(self):
        """Load spaCy en_core_web_sm for NER. Falls back to keyword list if unavailable."""
        if self.nlp is not None:
            return
        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("Graph RAG: spaCy NER model loaded (en_core_web_sm).")
            except OSError:
                print("Graph RAG: spaCy model not found — run 'python -m spacy download en_core_web_sm'. Using keyword fallback.")
                self.nlp = "fallback"
        except ImportError:
            print("Graph RAG: spaCy not installed — using keyword fallback.")
            self.nlp = "fallback"

    def _extract_entities(self, text: str) -> set[str]:
        """Return entity strings from a chunk using spaCy NER or keyword fallback."""
        if self.nlp == "fallback" or self.nlp is None:
            return self._keyword_entities(text)
        doc = self.nlp(text[:5000])
        entities: set[str] = set()
        for ent in doc.ents:
            if ent.label_ in RELEVANT_NER_LABELS:
                normalized = ent.text.strip().title()
                if len(normalized) > 2:
                    entities.add(normalized)
        return entities

    def _keyword_entities(self, text: str) -> set[str]:
        """Fallback: match a known entity list against the chunk."""
        known = {
            "Chad", "Niger", "Nigeria", "Sudan", "Libya", "Cameroon",
            "Central African Republic", "N'Djamena", "Lake Chad",
            "Sahel", "Sahara", "Africa", "France", "United Nations",
            "African Union", "Lake Chad Basin Commission",
            "Zakouma", "Ennedi", "Tibesti", "Ounianga",
        }
        text_lower = text.lower()
        return {e for e in known if e.lower() in text_lower}

    def _fetch_wikipedia(self) -> list[dict]:
        """Fetch Wikipedia pages: Chad core topics + all 6 bordering countries."""
        try:
            from langchain_community.document_loaders import WikipediaLoader
        except ImportError:
            raise ImportError("langchain-community is required. Run: pip install langchain-community wikipedia")

        documents: list[dict] = []
        seen_titles: set[str] = set()

        for query in CHAD_WIKI_PAGES:
            try:
                loader = WikipediaLoader(query=query, load_max_docs=1, doc_content_chars_max=15000)
                docs = loader.load()
                for doc in docs:
                    title = doc.metadata.get("title", query)
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)
                    documents.append({
                        "title": title,
                        "content": doc.page_content,
                        "url": doc.metadata.get("source", "https://en.wikipedia.org"),
                    })
                    print(f"  Fetched: {title} ({len(doc.page_content):,} chars)")
            except Exception as exc:
                print(f"  Warning: could not fetch '{query}': {exc}")

        return documents

    def _split_documents(self, documents: list[dict]) -> tuple[list[str], list[dict]]:
        """Chunk documents with LangChain RecursiveCharacterTextSplitter."""
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore[import-untyped]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks: list[str] = []
        metadata: list[dict] = []

        for doc in documents:
            for text in splitter.split_text(doc["content"]):
                stripped = text.strip()
                if len(stripped) >= 40:
                    chunks.append(stripped)
                    metadata.append({"title": doc["title"], "url": doc["url"]})

        return chunks, metadata

    def _build_graph(self) -> nx.Graph:
        """
        Build heterogeneous entity-relationship graph.

        Node types:
          "chunk"  — text chunk, index = position in self.chunks list
          "entity" — named entity, index = n_chunks + offset

        Edge types:
          "sequential"    — adjacent chunks within the same article
          "mentions"      — chunk → entity (chunk references that entity)
          "co-occurs"     — entity ↔ entity (both appear in the same chunk)
          "cross-country" — hardcoded geopolitical relations
        """
        G = nx.Graph()
        n_chunks = len(self.chunks)

        # --- Chunk nodes ---
        for i, (chunk, meta) in enumerate(zip(self.chunks, self.chunk_metadata)):
            G.add_node(i, node_type="chunk", text=chunk, title=meta["title"], url=meta["url"])

        # --- Sequential edges within same article ---
        doc_groups: dict[str, list[int]] = defaultdict(list)
        for i, meta in enumerate(self.chunk_metadata):
            doc_groups[meta["title"]].append(i)

        for nodes in doc_groups.values():
            for j in range(len(nodes) - 1):
                G.add_edge(nodes[j], nodes[j + 1], weight=2.0, edge_type="sequential")

        # --- NER pass: extract entities from every chunk ---
        print("Graph RAG: Running NER on chunks...")
        self._load_nlp()
        chunk_entities: list[set[str]] = []
        entity_freq: dict[str, int] = defaultdict(int)

        for chunk in self.chunks:
            ents = self._extract_entities(chunk)
            chunk_entities.append(ents)
            for e in ents:
                entity_freq[e] += 1

        # --- Entity nodes (appear in ≥ MIN_ENTITY_FREQ chunks) ---
        entity_node_id = n_chunks
        entity_to_node: dict[str, int] = {}

        for entity, freq in entity_freq.items():
            if freq >= MIN_ENTITY_FREQ:
                G.add_node(entity_node_id, node_type="entity", label=entity, freq=freq)
                entity_to_node[entity] = entity_node_id
                entity_node_id += 1

        self._entity_to_node = entity_to_node
        print(f"Graph RAG: {len(entity_to_node)} entity nodes created.")

        # --- Chunk → Entity mention edges ---
        for chunk_id, ents in enumerate(chunk_entities):
            for ent in ents:
                if ent in entity_to_node:
                    G.add_edge(chunk_id, entity_to_node[ent], weight=1.5, edge_type="mentions")

        # --- Entity co-occurrence edges ---
        for ents in chunk_entities:
            ent_list = [e for e in ents if e in entity_to_node]
            for i in range(len(ent_list)):
                for j in range(i + 1, len(ent_list)):
                    a, b = entity_to_node[ent_list[i]], entity_to_node[ent_list[j]]
                    if G.has_edge(a, b):
                        G[a][b]["weight"] += 1.0
                    else:
                        G.add_edge(a, b, weight=1.0, edge_type="co-occurs")

        # --- Explicit cross-country relationship edges ---
        wired = 0
        for src, relation, tgt in CROSS_COUNTRY_RELATIONS:
            src_id = entity_to_node.get(src.title())
            tgt_id = entity_to_node.get(tgt.title())
            if src_id is not None and tgt_id is not None:
                if G.has_edge(src_id, tgt_id):
                    existing = G[src_id][tgt_id].get("relations", [])
                    G[src_id][tgt_id]["relations"] = existing + [relation]
                    G[src_id][tgt_id]["weight"] += 3.0
                else:
                    G.add_edge(src_id, tgt_id, weight=3.0, edge_type="cross-country", relations=[relation])
                wired += 1

        print(f"Graph RAG: {wired} cross-country relation edges wired.")
        return G

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize(self, force_refresh: bool = False):
        """Build the entity-relationship graph. Thread-safe; caches to disk."""
        with self._lock:
            if self._initialized and not force_refresh:
                return

            try:
                # ---- Try cache first ----
                if not force_refresh and os.path.exists(CACHE_FILE):
                    try:
                        print("Graph RAG: Loading from cache...")
                        with open(CACHE_FILE, "rb") as f:
                            cache = pickle.load(f)
                        if cache.get("version") != CACHE_VERSION:
                            raise ValueError(f"Cache version {cache.get('version')} != {CACHE_VERSION}")
                        self.chunks = cache["chunks"]
                        self.chunk_metadata = cache["metadata"]
                        self.embeddings = cache["embeddings"].astype(np.float32)
                        self.graph = cache["graph"]
                        self._entity_to_node = cache.get("entity_to_node", {})
                        self._load_embedder()
                        self._initialized = True
                        n_entities = sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "entity")
                        print(
                            f"Graph RAG: Ready from cache — "
                            f"{len(self.chunks)} chunks, "
                            f"{n_entities} entity nodes, "
                            f"{self.graph.number_of_nodes()} total nodes, "
                            f"{self.graph.number_of_edges()} edges"
                        )
                        return
                    except Exception as cache_exc:
                        print(f"Graph RAG: Cache invalid ({cache_exc}), rebuilding...")
                        self.chunks = []
                        self.chunk_metadata = []
                        self.embeddings = None
                        self.graph = nx.Graph()

                # ---- Fresh build ----
                print("Graph RAG: Fetching Wikipedia (Chad + neighboring countries)...")
                self._load_embedder()

                documents = self._fetch_wikipedia()
                if not documents:
                    print("Graph RAG: No documents fetched; graph RAG disabled.")
                    self._initialized = True
                    return

                print(f"Graph RAG: Splitting {len(documents)} articles...")
                self.chunks, self.chunk_metadata = self._split_documents(documents)
                print(f"Graph RAG: {len(self.chunks)} chunks created.")

                print("Graph RAG: Computing embeddings...")
                self.embeddings = np.array(
                    self.embedder.encode(self.chunks, show_progress_bar=False),
                    dtype=np.float32,
                )

                print("Graph RAG: Building entity-relationship graph...")
                self.graph = self._build_graph()
                n_entities = sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "entity")
                print(
                    f"Graph RAG: Graph built — "
                    f"{self.graph.number_of_nodes()} nodes "
                    f"({len(self.chunks)} chunks + {n_entities} entities), "
                    f"{self.graph.number_of_edges()} edges."
                )

                # ---- Persist cache ----
                try:
                    with open(CACHE_FILE, "wb") as f:
                        pickle.dump({
                            "version": CACHE_VERSION,
                            "chunks": self.chunks,
                            "metadata": self.chunk_metadata,
                            "embeddings": self.embeddings,
                            "graph": self.graph,
                            "entity_to_node": self._entity_to_node,
                        }, f)
                    print("Graph RAG: Cache saved.")
                except Exception as exc:
                    print(f"Graph RAG: Cache save failed: {exc}")

                self._initialized = True
                print("Graph RAG: Ready!")

            except Exception as exc:
                import traceback
                self._init_error = str(exc)
                self._initialized = True
                print(f"Graph RAG: Initialization failed: {exc}")
                traceback.print_exc()

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Entity-aware graph retrieval:
          1. Cosine similarity → top-k seed chunk nodes
          2. seed chunks → entity nodes (via "mentions" edges)
          3. entity nodes → bridged chunk nodes (entity-linked retrieval)
          4. Cross-country edges ensure related-country chunks surface
          5. Sequential 1-hop expansion for adjacent context
        """
        if not self.chunks or self.embeddings is None:
            return []

        self._load_embedder()

        q_emb = np.array(
            self.embedder.encode([query], show_progress_bar=False),
            dtype=np.float32,
        )

        emb_norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norm_embs = self.embeddings / (emb_norms + 1e-8)
        q_norm = q_emb / (np.linalg.norm(q_emb) + 1e-8)
        scores = (norm_embs @ q_norm.T).flatten()

        top_idx = np.argsort(scores)[::-1][:top_k]
        seed_set = {int(i) for i in top_idx}
        seed_scores = {int(i): float(scores[i]) for i in top_idx}

        # Step 2+3: chunk → entity → chunk bridging
        bridged: set[int] = set()
        for chunk_id in seed_set:
            if not self.graph.has_node(chunk_id):
                continue
            for entity_id in list(self.graph.neighbors(chunk_id)):
                if self.graph.nodes[entity_id].get("node_type") != "entity":
                    continue
                # Cross-country hop: follow entity→entity cross-country edges
                for linked_entity_id in list(self.graph.neighbors(entity_id)):
                    if self.graph.nodes[linked_entity_id].get("node_type") != "entity":
                        continue
                    edge_data = self.graph[entity_id][linked_entity_id]
                    if edge_data.get("edge_type") == "cross-country":
                        # Collect chunks linked to the cross-country entity
                        for cross_chunk_id in self.graph.neighbors(linked_entity_id):
                            if (self.graph.nodes[cross_chunk_id].get("node_type") == "chunk"
                                    and cross_chunk_id not in seed_set):
                                bridged.add(cross_chunk_id)
                # Standard entity-bridged retrieval
                for neighbor_id in self.graph.neighbors(entity_id):
                    if (self.graph.nodes[neighbor_id].get("node_type") == "chunk"
                            and neighbor_id not in seed_set):
                        bridged.add(neighbor_id)

        # Step 5: sequential 1-hop expansion
        expanded_seq: set[int] = set()
        for node in seed_set:
            if self.graph.has_node(node):
                for neighbor, edata in self.graph[node].items():
                    if (self.graph.nodes[neighbor].get("node_type") == "chunk"
                            and edata.get("weight", 0) >= 2):
                        expanded_seq.add(neighbor)

        results: list[dict] = []
        seen: set[int] = set()
        ordered = (
            list(seed_set)
            + [n for n in bridged if n not in seed_set]
            + [n for n in expanded_seq if n not in seed_set and n not in bridged]
        )

        for node_id in ordered:
            if node_id in seen or node_id >= len(self.chunks):
                continue
            seen.add(node_id)
            results.append({
                "text": self.chunks[node_id],
                "title": self.chunk_metadata[node_id]["title"],
                "url": self.chunk_metadata[node_id]["url"],
                "score": seed_scores.get(node_id, 0.30),
                "via_graph": node_id not in seed_set,
            })

        return results[: top_k + 5]

    def get_stats(self) -> dict:
        """Return diagnostic information about the graph."""
        n_entities = sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "entity")
        articles = sorted({m["title"] for m in self.chunk_metadata})
        return {
            "initialized": self._initialized,
            "error": self._init_error,
            "chunks": len(self.chunks),
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "entity_nodes": n_entities,
            "articles": articles,
        }

    @property
    def ready(self) -> bool:
        return self._initialized and bool(self.chunks)


# ---------------------------------------------------------------------------
# Module-level singleton + background initialiser
# ---------------------------------------------------------------------------

_instance: ChadGraphRAG | None = None
_init_thread: threading.Thread | None = None


def get_graph_rag() -> ChadGraphRAG:
    global _instance
    if _instance is None:
        _instance = ChadGraphRAG()
    return _instance


def init_graph_rag_async():
    """Start background Wikipedia fetch + entity-graph build (non-blocking)."""
    global _init_thread
    rag = get_graph_rag()
    if not rag._initialized:
        _init_thread = threading.Thread(target=rag.initialize, daemon=True, name="GraphRAGInit")
        _init_thread.start()
        print("Graph RAG: Background initialization started.")


