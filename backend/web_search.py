"""
Lightweight web search fallback for the Chad RAG pipeline.
Uses DuckDuckGo (no API key required) via the duckduckgo-search package.

Returned results are raw enough to be fed directly into the LLM context.
"""

import re
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from ddgs import DDGS

try:
    from ddgs import DDGS  # type: ignore[assignment]  # noqa: F811
    _DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS  # type: ignore[assignment, no-redef]  # noqa: F811
        _DDGS_AVAILABLE = True
    except ImportError:
        _DDGS_AVAILABLE = False


class WebResult(TypedDict):
    title: str
    url: str
    snippet: str


# Signals that the question likely needs current/web information
_RECENCY_PATTERNS = re.compile(
    r'\b(current|latest|recent|today|now|2024|2025|2026|news|update|last (week|month|year))\b',
    re.IGNORECASE,
)


def needs_web_search(question: str, graph_result_count: int) -> bool:
    """
    Return True if web search should be triggered.
    Two conditions:
      1. Graph RAG returned fewer than 2 results (topic likely not in Wikipedia corpus).
      2. Question contains recency signals ('current', 'latest', '2025', etc.).
    """
    if not _DDGS_AVAILABLE:
        return False
    if graph_result_count < 2:
        return True
    if _RECENCY_PATTERNS.search(question):
        return True
    return False


def search_web(query: str, max_results: int = 4) -> list[WebResult]:
    """
    Search DuckDuckGo for `query` and return up to `max_results` snippets.
    Automatically appends "Chad Africa" to improve relevance.
    Returns an empty list on any failure.
    """
    if not _DDGS_AVAILABLE:
        return []

    # Ensure results are Chad-focused unless the query is already specific
    search_query = query if 'chad' in query.lower() else f"{query} Chad Africa"

    try:
        with DDGS() as ddgs:
            raw = ddgs.text(search_query, max_results=max_results, safesearch='off')
            results: list[WebResult] = []
            for item in raw:
                title = item.get('title', '')
                url = item.get('href', item.get('url', ''))
                snippet = item.get('body', item.get('snippet', ''))
                if title and snippet:
                    results.append({'title': title, 'url': url, 'snippet': snippet})
            return results
    except Exception as exc:
        print(f'[web_search] DuckDuckGo error: {exc}')
        return []
