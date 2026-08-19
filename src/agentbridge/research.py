"""Deterministic validation for model-produced research evidence."""

from __future__ import annotations

from typing import Any

from agentbridge.graph.helpers import dedupe_sources
from agentbridge.schemas import FrameworkResearchResult


def validate_research_evidence(result: FrameworkResearchResult) -> dict[str, list[dict[str, Any]] | list[str]]:
    """Keep only facts that cite one of the normalized, non-empty source URLs."""
    sources = dedupe_sources([source.model_dump() for source in result.sources])
    known_urls = {source["url"] for source in sources}
    facts = [fact.model_dump() for fact in result.raw_framework_facts if fact.source_url in known_urls]
    return {
        "research_queries": result.research_queries,
        "research_sources": sources,
        "raw_framework_facts": facts,
    }
