"""Deterministic validation for model-produced research evidence."""

from __future__ import annotations

from typing import Any

from agentbridge.graph.helpers import dedupe_sources
from agentbridge.schemas import FrameworkResearchResult
from agentbridge.source_urls import normalize_source_url


def validate_research_evidence(result: FrameworkResearchResult) -> dict[str, list[dict[str, Any]] | list[str]]:
    """Keep only facts that cite one of the normalized, non-empty source URLs."""
    normalized_sources = []
    for source in result.sources:
        url = normalize_source_url(source.url)
        if not url:
            continue
        source_record = source.model_dump()
        source_record["url"] = url
        normalized_sources.append(source_record)

    sources = dedupe_sources(normalized_sources)
    known_urls = {source["url"] for source in sources}
    facts = []
    for fact in result.raw_framework_facts:
        source_url = normalize_source_url(fact.source_url)
        if source_url not in known_urls:
            continue
        fact_record = fact.model_dump()
        fact_record["source_url"] = source_url
        facts.append(fact_record)

    return {
        "research_queries": result.research_queries,
        "research_sources": sources,
        "raw_framework_facts": facts,
    }
