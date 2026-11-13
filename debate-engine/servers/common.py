"""Shared web-search helper used by the optimist / skeptic / risk servers.

Backends, in order:
  1. Tavily  (if TAVILY_API_KEY is set)
  2. DuckDuckGo (no key, via the duckduckgo-search / ddgs package)
  3. A clear "no search available" message (so the pipeline still runs)
"""
import os
import json
import httpx


def _tavily(query: str, n: int):
    r = httpx.post(
        "https://api.tavily.com/search",
        json={"api_key": os.environ["TAVILY_API_KEY"], "query": query,
              "max_results": n, "search_depth": "basic"},
        timeout=20,
    )
    r.raise_for_status()
    return [{"title": x.get("title", ""), "snippet": x.get("content", "")[:350],
             "url": x.get("url", "")} for x in r.json().get("results", [])]


def _ddg(query: str, n: int):
    try:
        from ddgs import DDGS  # newer package name
    except ImportError:
        from duckduckgo_search import DDGS
    with DDGS() as d:
        rows = list(d.text(query, max_results=n))
    return [{"title": x.get("title", ""), "snippet": x.get("body", "")[:350],
             "url": x.get("href", "")} for x in rows]


def web_search(query: str, n: int = 5) -> str:
    """Returns a JSON string: {"query":..., "backend":..., "results":[...]}"""
    errors = []
    if os.getenv("TAVILY_API_KEY"):
        try:
            return json.dumps({"query": query, "backend": "tavily", "results": _tavily(query, n)})
        except Exception as e:
            errors.append(f"tavily: {e}")
    try:
        return json.dumps({"query": query, "backend": "duckduckgo", "results": _ddg(query, n)})
    except Exception as e:
        errors.append(f"duckduckgo: {e}")
    return json.dumps({
        "query": query, "backend": "none", "results": [],
        "note": "No search backend worked. State clearly that you have no live evidence.",
        "errors": errors,
    })
