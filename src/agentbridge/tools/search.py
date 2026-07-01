"""Search tool and result normalization."""

from __future__ import annotations

from typing import Any, Protocol

from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper

from agentbridge.schemas import SourceItem


class SearchClient(Protocol):
    k: int

    def results(self, query: str) -> dict[str, Any]:
        ...


def classify_source(url: str) -> tuple[str, str]:
    url_lower = (url or "").lower()
    if "github.com" in url_lower:
        return "github", "high"
    if "docs." in url_lower or "/docs" in url_lower or "documentation" in url_lower:
        return "official_docs", "high"
    if "release" in url_lower or "changelog" in url_lower:
        return "release_notes", "high"
    if any(host in url_lower for host in ["medium.com", "substack.com", "dev.to"]):
        return "technical_blog", "medium"
    return "other", "medium"


def normalize_search_results(results: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    sources = []
    for item in results.get("organic", [])[:limit]:
        url = item.get("link", "")
        source_type, reliability = classify_source(url)
        sources.append(
            SourceItem(
                title=item.get("title") or "Untitled",
                url=url,
                summary=(item.get("snippet") or "").replace("\n", " "),
                source_type=source_type,
                reliability=reliability,
            ).model_dump()
        )
    return sources


def build_serper_client(*, k: int = 5) -> GoogleSerperAPIWrapper:
    return GoogleSerperAPIWrapper(k=k)


def search_sources(query: str, *, search_client: SearchClient | None = None) -> list[dict[str, Any]]:
    search_client = search_client or build_serper_client()
    return normalize_search_results(search_client.results(query), limit=search_client.k)


def build_search_tool(*, search_client: SearchClient | None = None):
    @tool
    def search_web(query: str) -> str:
        """Search the web for current information. Returns titles, URLs, and snippets to cite as sources."""
        sources = search_sources(query, search_client=search_client)
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
