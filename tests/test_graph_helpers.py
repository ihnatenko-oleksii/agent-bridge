from types import SimpleNamespace

from langchain_core.messages import AIMessage

from agentbridge.graph.helpers import (
    dedupe_sources,
    format_graph_result,
    format_interrupt_payload,
    get_search_tool_outputs,
    resume_value_to_text,
)


def test_resume_value_to_text_for_dict():
    assert resume_value_to_text({"team": "python", "cloud": "aws"}) == "team: python\ncloud: aws"


def test_dedupe_sources_respects_first_url():
    sources = [
        {"url": "https://a.example", "title": "A"},
        {"url": "https://a.example", "title": "A2"},
        {"url": "https://b.example", "title": "B"},
    ]
    assert dedupe_sources(sources) == [
        {"url": "https://a.example", "title": "A"},
        {"url": "https://b.example", "title": "B"},
    ]


def test_format_interrupt_payload():
    payload = {"message": "Need info", "questions": ["What stack?", "What data?"]}
    assert format_interrupt_payload(payload) == "Need info\n\n- What stack?\n- What data?"


def test_format_graph_result_prefers_final_recommendation():
    result = {"final_recommendation": "Use LangGraph", "messages": [AIMessage(content="fallback")]}
    assert format_graph_result(result) == "Use LangGraph"


def test_get_search_tool_outputs_matches_queries():
    messages = [
        SimpleNamespace(tool_calls=[{"name": "search_web", "id": "1", "args": {"query": "langgraph"}}]),
        SimpleNamespace(type="tool", name="search_web", tool_call_id="1", content="Query: langgraph"),
    ]
    assert get_search_tool_outputs(messages) == [{"query": "langgraph", "output": "Query: langgraph"}]
