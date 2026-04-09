"""
ChadGPT — Flask API server.

Endpoints:
  POST /api/graph-ask    — Entity-graph RAG + web fallback + multi-turn history
  GET  /api/graph-stats  — Knowledge graph diagnostics
  POST /api/graph-refresh — Force-rebuild the Wikipedia graph
  GET  /api/analyze      — scikit-learn chart data for a topic
"""

import os
import re
import threading
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

from graph_rag import get_graph_rag, init_graph_rag_async
from data_analysis import get_charts_for_topic
from web_search import needs_web_search, search_web

load_dotenv(Path(__file__).resolve().parent.parent / '.env')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODELS = [
    'nvidia/nemotron-3-super-120b-a12b:free',
    'meta-llama/llama-3.3-70b-instruct:free',
    'mistralai/mistral-7b-instruct:free',
]

# Reusable HTTP session for connection pooling
_session = requests.Session()
_session.headers.update({
    'Authorization': f'Bearer {OPENROUTER_API_KEY}',
    'Content-Type': 'application/json',
    'HTTP-Referer': 'https://chadgpt.local',
    'X-Title': 'Chad Graph RAG',
})


def _parse_llm_response(raw: str) -> tuple[str, str | None]:
    """Extract (clean_answer, topic_title) from raw LLM text.

    The LLM is instructed to append:
        Source: <article title>
        Topic: <2-5 word summary>
    This function strips the Topic line and returns it separately.
    """
    topic: str | None = None
    topic_match = re.search(r'\nTopic:\s*(.+)', raw)
    if topic_match:
        topic = topic_match.group(1).strip()
        raw = raw[:topic_match.start()].rstrip()
    return raw.strip(), topic


app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})


_CHAD_SUBJECT = re.compile(
    r"chad(?:ian)?|n['\u2019]?djamena|ndjamena|zakouma|tibesti|ennedi|lake\s+chad",
    re.IGNORECASE,
)
_OTHER_COUNTRY = re.compile(
    r"\b(france|usa|nigeria|libya|sudan|niger|cameroon|india|china)\b",
    re.IGNORECASE,
)


def is_about_chad(query: str) -> bool:
    if _CHAD_SUBJECT.search(query):
        return True
    if _OTHER_COUNTRY.search(query):
        return False
    return True


_VIZ_PATTERNS = re.compile(
    r'\b(graph|chart|plot|visuali[sz]e?|show.{0,20}data|trend|statistics|diagram|visual|display.{0,10}data)\b',
    re.IGNORECASE,
)


def is_visualization_request(question: str) -> bool:
    """Return True when the user is asking for a chart or data visualization."""
    return bool(_VIZ_PATTERNS.search(question))


@app.route('/api/graph-stats', methods=['GET'])
def graph_stats():
    """Return statistics about the Wikipedia knowledge graph."""
    return jsonify(get_graph_rag().get_stats())


@app.route('/api/graph-ask', methods=['POST'])
def graph_ask():
    """
    Graph RAG-only endpoint: retrieves from Wikipedia knowledge graph
    and feeds results to the LLM.  Falls back to local KB if graph not ready.
    Accepts optional `history` list of {role, content} for multi-turn context.
    """
    data = request.json
    question = data.get('question', '')
    history: list[dict] = data.get('history', [])
    show_viz = is_visualization_request(question)

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    if not is_about_chad(question):
        return jsonify({
            'answer': "I'm specialized in providing information about Chad only.",
            'title': None,
            'sources': [],
            'graph_sources': [],
            'show_visualization': False,
        })

    graph_rag = get_graph_rag()
    graph_sources: list[dict] = []

    if not graph_rag.ready:
        return jsonify({
            'answer': 'The knowledge graph is still initializing. Please try again in a moment.',
            'title': None,
            'sources': [],
            'graph_sources': [],
            'web_sources': [],
            'show_visualization': False,
        })

    graph_results = graph_rag.search(question, top_k=5)
    context = "You are an expert on the Republic of Chad. Use the following Wikipedia-sourced information:\n\n"
    seen_titles: set[str] = set()
    for r in graph_results:
        context += f"[WIKIPEDIA — {r['title']}]\n{r['text']}\n\n"
        if r['title'] not in seen_titles:
            seen_titles.add(r['title'])
            graph_sources.append({'title': r['title'], 'url': r['url']})

    # Web search fallback — fires when graph has low coverage or question is time-sensitive
    web_sources: list[dict] = []
    if needs_web_search(question, len(graph_results)):
        web_results = search_web(question, max_results=4)
        if web_results:
            context += "The following results were retrieved from the web to supplement the Wikipedia context:\n\n"
            for w in web_results:
                context += f"[WEB — {w['title']}]\n{w['snippet']}\n\n"
                web_sources.append({'title': w['title'], 'url': w['url']})

    system_prompt = (
        "You are ChadGPT, an expert assistant on the Republic of Chad in Africa.\n\n"
        "RULES:\n"
        "- Answer directly and concisely. Output ONLY the final answer.\n"
        "- Do NOT show your reasoning or thinking process.\n"
        "- Do NOT use phrases like \"Let me think...\", \"First I will...\", \"Step 1:\", \"Therefore...\", \"Based on the context...\".\n"
        "- Do NOT explain how you arrived at the answer.\n"
        "- Do NOT list the rules you are following.\n"
        "- ONLY answer questions about Chad. If asked about other topics, say so briefly.\n"
        "- After your answer, cite your source on a new line in the format: Source: <title>\n"
        "- After the source, write a 2-5 word topic title on a new line in the format: Topic: <title>\n"
    )
    if show_viz:
        system_prompt += (
            "- The user is requesting a chart or visualization. After your answer, add this exact sentence "
            "on a new line: 'Please check the **Data Visualization** panel — I have loaded charts for your query.'\n"
        )

    # Few-shot examples to enforce output format
    few_shot = [
        {'role': 'user', 'content': 'What is the capital of Chad?'},
        {'role': 'assistant', 'content': "The capital of Chad is N'Djamena, located at the confluence of the Chari and Logone rivers near the western border with Cameroon.\n\nSource: Chad (Wikipedia)\nTopic: Capital city of Chad"},
        {'role': 'user', 'content': 'How big is Lake Chad?'},
        {'role': 'assistant', 'content': "Lake Chad was once one of Africa's largest lakes, covering around 25,000 km² in the 1960s, but has shrunk by roughly 90% due to climate change and water diversion. Today it covers approximately 1,350 km².\n\nSource: Lake Chad (Wikipedia)\nTopic: Lake Chad size and shrinkage"},
        {'role': 'user', 'content': 'Tell me about France.'},
        {'role': 'assistant', 'content': "I'm specialized in providing information about Chad only. However, France has a significant historical connection to Chad as the former colonial power — Chad gained independence from France on August 11, 1960.\n\nSource: History of Chad (Wikipedia)\nTopic: Chad independence from France"},
    ]

    messages = [
        {'role': 'system', 'content': system_prompt + "\nKnowledge Base Context:\n" + context},
        *few_shot,
        *[{'role': turn['role'], 'content': turn['content']} for turn in history[-10:] if turn.get('role') in ('user', 'assistant')],
        {'role': 'user', 'content': question},
    ]

    for model in OPENROUTER_MODELS:
        try:
            resp = _session.post(
                'https://openrouter.ai/api/v1/chat/completions',
                json={
                    'model': model,
                    'messages': messages,
                    'temperature': 0.2,
                    'max_tokens': 2048,
                },
                timeout=30,
            )
            if resp.status_code == 402:
                print(f'Graph-ask: {model} returned 402 (credit limit), trying next model.')
                continue
            if resp.status_code == 200:
                body = resp.json()
                if 'choices' in body and body['choices']:
                    raw = body['choices'][0].get('message', {}).get('content', '')
                    if raw:
                        answer, title = _parse_llm_response(raw)
                        return jsonify({
                            'answer': answer,
                            'title': title,
                            'sources': list(seen_titles),
                            'graph_sources': graph_sources,
                            'web_sources': web_sources,
                            'show_visualization': show_viz,
                        })
        except Exception as exc:
            print(f'Graph-ask API error ({model}): {exc}')

    # Fallback: build answer from graph results directly
    answer = "Based on Wikipedia sources:\n\n"
    for r in graph_results[:3]:
        sentences = r['text'].split('.')[:3]
        answer += '.'.join(sentences) + '.\n\n'
    return jsonify({
        'answer': answer.strip(),
        'title': None,
        'sources': list(seen_titles),
        'graph_sources': graph_sources,
        'web_sources': web_sources,
        'show_visualization': show_viz,
    })


@app.route('/api/graph-refresh', methods=['POST'])
def graph_refresh():
    """Force-rebuild the Wikipedia knowledge graph (clears cache)."""
    t = threading.Thread(
        target=lambda: get_graph_rag().initialize(force_refresh=True),
        daemon=True,
        name='GraphRAGRefresh',
    )
    t.start()
    return jsonify({'status': 'Graph RAG refresh started in background'})


@app.route('/api/analyze', methods=['GET'])
def analyze():
    """Return scikit-learn chart data for a given topic and optional raw query."""
    topic = request.args.get('topic', 'general').lower()
    query = request.args.get('q', '').strip()
    try:
        result = get_charts_for_topic(topic, query=query)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'charts': []}), 500


# Start Graph RAG background initialization only in the actual serving process.
#
# Process matrix:
#   flask run --debug  → parent watcher: FLASK_RUN_FROM_CLI=true, WERKZEUG_RUN_MAIN=None  → SKIP
#                      → child worker:  FLASK_RUN_FROM_CLI=true, WERKZEUG_RUN_MAIN=true   → INIT
#   python server.py   → use_reloader=False, so only one process:  WERKZEUG_RUN_MAIN=None → INIT
#   gunicorn/prod      → no werkzeug env vars                                            → INIT
_in_reloader_child = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
_in_direct_run = (
    os.environ.get('WERKZEUG_RUN_MAIN') is None
    and os.environ.get('FLASK_RUN_FROM_CLI') != 'true'
)
if _in_reloader_child or _in_direct_run:
    init_graph_rag_async()


if __name__ == '__main__':
    print("ChadGPT backend — http://localhost:8000")
    # use_reloader=False prevents Werkzeug from spawning a second process,
    # which would cause the graph RAG to be initialized twice.
    app.run(debug=True, host="0.0.0.0", port=8000, use_reloader=False)
