"""Search tool and result normalization."""

from __future__ import annotations

import json
from typing import Any, Protocol
from urllib.parse import urlsplit

from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper

from agentbridge.schemas import SourceItem
from agentbridge.source_urls import normalize_source_url


class SearchClient(Protocol):
    k: int

    def results(self, query: str) -> dict[str, Any]: ...


def classify_source(url: str) -> tuple[str, str]:
    parsed = urlsplit(url or "")
    hostname = (parsed.hostname or "").lower().rstrip(".")
    path_segments = {segment.lower() for segment in parsed.path.split("/") if segment}

    if hostname == "github.com" or hostname.endswith(".github.com") or hostname.endswith(".githubusercontent.com"):
        return "github", "high"
    if hostname.startswith("docs.") or {"docs", "documentation"} & path_segments:
        return "official_docs", "high"
    if {"release", "releases", "changelog"} & path_segments:
        return "release_notes", "high"
    if any(hostname == host or hostname.endswith(f".{host}") for host in ["medium.com", "substack.com", "dev.to"]):
        return "technical_blog", "medium"
    return "other", "medium"


def _is_http_url(value: Any) -> bool:
    return normalize_source_url(value) is not None


def _clean_text(value: Any, *, default: str) -> str:
    if not isinstance(value, str):
        return default
    return " ".join(value.split()) or default


def normalize_search_results(results: Any, *, limit: int) -> list[dict[str, Any]]:
    """Convert a Serper response into safe, consistently shaped source records."""
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        return []
    if not isinstance(results, dict) or not isinstance(results.get("organic", []), list):
        return []

    sources = []
    seen_urls: set[str] = set()
    for item in results["organic"]:
        if len(sources) >= limit:
            break
        if not isinstance(item, dict):
            continue
        url = normalize_source_url(item.get("link"))
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        source_type, reliability = classify_source(url)
        sources.append(
            SourceItem(
                title=_clean_text(item.get("title"), default="Untitled"),
                url=url,
                summary=_clean_text(item.get("snippet"), default=""),
                source_type=source_type,
                reliability=reliability,
            ).model_dump()
        )
    return sources


def build_serper_client(*, k: int = 5) -> GoogleSerperAPIWrapper:
    return GoogleSerperAPIWrapper(k=k)


def search_sources(query: str, *, search_client: SearchClient | None = None) -> list[dict[str, Any]]:
    if not isinstance(query, str) or not query.strip():
        return []
    query = query.strip()
    search_client = search_client or build_serper_client()
    return normalize_search_results(search_client.results(query), limit=search_client.k)


def build_search_tool(*, search_client: SearchClient | None = None):
    @tool
    def search_web(query: str) -> str:
        """Search the web for current information. Returns titles, URLs, and snippets to cite as sources."""
        try:
            sources = search_sources(query, search_client=search_client)
        except Exception as exc:
            return json.dumps({"query": query, "error": f"Search provider failed: {type(exc).__name__}"})
        if not sources:
            return f"Query: {query}\nNo search results found."

        lines = [f"Query: {query}", ""]
        for index, source in enumerate(sources, 1):
            lines.extend(
                [
                    f"[{index}] {source['title']}",
                    f"URL: {source['url']}",
                    f"Snippet: {source['summary']}",
                    f"Reliability: {source['reliability']}",
                    "",
                ]
            )
        return "\n".join(lines)

    return search_web
