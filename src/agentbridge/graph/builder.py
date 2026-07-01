"""Graph construction and compilation."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agentbridge.graph.nodes import create_nodes, route_after_framework_research, route_after_input_check
from agentbridge.llm import build_llm
from agentbridge.schemas import AgentBridgeState
from agentbridge.tools.search import build_search_tool


def build_graph(*, llm=None, search_tool=None, checkpointer=None):
    llm = llm or build_llm()
    search_tool = search_tool or build_search_tool()
    checkpointer = checkpointer or MemorySaver()

    nodes = create_nodes(llm, search_tool)

    graph_builder = StateGraph(AgentBridgeState)
    graph_builder.add_node("input_check", nodes.input_check)
    graph_builder.add_node("client_context_extractor", nodes.client_context_extractor)
    graph_builder.add_node("framework_research", nodes.framework_research)
    graph_builder.add_node("research_tools", ToolNode([search_tool]))
    graph_builder.add_node("framework_analyst", nodes.framework_analyst)
    graph_builder.add_node("comparison", nodes.comparison)
    graph_builder.add_node("recommendation_writer", nodes.recommendation_writer)

    graph_builder.add_edge(START, "input_check")
    graph_builder.add_conditional_edges(
        "input_check",
        route_after_input_check,
        {
            "ready": "client_context_extractor",
            "needs_more_context": END,
        },
    )
    graph_builder.add_edge("client_context_extractor", "framework_research")
    graph_builder.add_conditional_edges(
        "framework_research",
        route_after_framework_research,
        {
            "research_tools": "research_tools",
            "framework_analyst": "framework_analyst",
        },
    )
    graph_builder.add_edge("research_tools", "framework_research")
    graph_builder.add_edge("framework_analyst", "comparison")
    graph_builder.add_edge("comparison", "recommendation_writer")
    graph_builder.add_edge("recommendation_writer", END)

    return graph_builder.compile(checkpointer=checkpointer)
