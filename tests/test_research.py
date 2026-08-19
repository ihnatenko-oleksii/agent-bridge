from agentbridge.research import validate_research_evidence
from agentbridge.schemas import FrameworkResearchResult, RawFrameworkFact, SourceItem


def test_validate_research_evidence_removes_uncited_claims_and_duplicate_sources():
    source = SourceItem(title="Docs", url="https://docs.example.com/framework", reliability="high")
    result = FrameworkResearchResult(
        research_queries=["framework docs"],
        sources=[source, source],
        raw_framework_facts=[
            RawFrameworkFact(framework="Example", fact="Has durable state", source_url=source.url),
            RawFrameworkFact(framework="Other", fact="Unsupported claim", source_url="https://invented.example"),
        ],
    )

    evidence = validate_research_evidence(result)

    assert len(evidence["research_sources"]) == 1
    assert evidence["raw_framework_facts"] == [
        {
            "framework": "Example",
            "fact": "Has durable state",
            "source_url": source.url,
            "reliability": "medium",
        }
    ]
