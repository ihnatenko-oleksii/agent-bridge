from langchain_core.messages import AIMessage

from agentbridge.graph.builder import build_graph
from agentbridge.graph.nodes import create_nodes, route_after_framework_research, route_after_input_check
from agentbridge.schemas import AgentBridgeState
from agentbridge.tools.search import build_search_tool


class FakeLLM:
    def with_structured_output(self, schema):
        return self

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(content="stub", tool_calls=[])


class ToolPlanningLLM(FakeLLM):
    def invoke(self, messages):
        return AIMessage(
            content="plan",
            tool_calls=[
                {"name": "unsupported_tool", "args": {}, "id": "unsupported"},
                {"name": "search_web", "args": {"query": "  framework docs  "}, "id": "docs"},
                {"name": "search_web", "args": {"query": "framework releases"}, "id": "releases"},
                {"name": "search_web", "args": {"query": "third query"}, "id": "third"},
                {"name": "search_web", "args": {"query": ""}, "id": "empty"},
            ],
        )


def test_route_after_input_check():
    assert route_after_input_check(AgentBridgeState(input_check_passed=True)) == "ready"
    assert route_after_input_check(AgentBridgeState(input_check_passed=False)) == "needs_more_context"


def test_route_after_framework_research():
    with_tool_call = AgentBridgeState(
        messages=[AIMessage(content="", tool_calls=[{"name": "search_web", "args": {"query": "x"}, "id": "1"}])]
    )
    without_tool_call = AgentBridgeState(messages=[AIMessage(content="done")])

    assert route_after_framework_research(with_tool_call) == "research_tools"
    assert route_after_framework_research(without_tool_call) == "framework_analyst"


def test_route_after_framework_research_ignores_unsupported_tool_calls():
    unsupported_tool_call = AgentBridgeState(
        messages=[AIMessage(content="", tool_calls=[{"name": "unsupported_tool", "args": {}, "id": "1"}])]
    )

    assert route_after_framework_research(unsupported_tool_call) == "framework_analyst"


def test_create_nodes_accepts_fake_dependencies():
    nodes = create_nodes(FakeLLM(), build_search_tool(search_client=None))
    assert callable(nodes.input_check)
    assert callable(nodes.framework_research)


def test_framework_research_bounds_and_sanitizes_tool_calls():
    nodes = create_nodes(ToolPlanningLLM(), build_search_tool(search_client=None))

    result = nodes.framework_research(AgentBridgeState(client_context={}))

    assert [
        (call["name"], call["args"]["query"], call["id"])
        for call in result["messages"][0].tool_calls
    ] == [
        ("search_web", "framework docs", "docs"),
        ("search_web", "framework releases", "releases"),
    ]


def test_build_graph_compiles_with_fake_dependencies():
    graph = build_graph(llm=FakeLLM(), search_tool=build_search_tool(search_client=None))
    assert graph is not None
