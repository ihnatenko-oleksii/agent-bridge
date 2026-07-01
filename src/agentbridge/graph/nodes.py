"""LangGraph node construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from agentbridge.config import MAX_SEARCH_CALLS
from agentbridge.graph.helpers import (
    as_compact_json,
    dedupe_sources,
    get_search_tool_outputs,
    get_user_question,
    resume_value_to_text,
)
from agentbridge.prompts import (
    CLIENT_CONTEXT_SYSTEM_PROMPT,
    COMPARISON_SYSTEM_PROMPT,
    FRAMEWORK_ANALYST_SYSTEM_PROMPT,
    INPUT_CHECK_SYSTEM_PROMPT,
    RECOMMENDATION_WRITER_SYSTEM_PROMPT,
    RESEARCH_FACT_SYSTEM_PROMPT,
    RESEARCH_TOOL_SYSTEM_PROMPT,
)
from agentbridge.schemas import (
    AgentBridgeState,
    ClientContextResult,
    FrameworkComparison,
    FrameworkProfilesResult,
    FrameworkResearchResult,
    InputCheckResult,
)


@dataclass(slots=True)
class GraphNodes:
    input_check: Any
    client_context_extractor: Any
    framework_research: Any
    framework_analyst: Any
    comparison: Any
    recommendation_writer: Any


def route_after_input_check(state: AgentBridgeState) -> str:
    return "ready" if state.input_check_passed else "needs_more_context"


def route_after_framework_research(state: AgentBridgeState) -> str:
    last_message = state.messages[-1] if state.messages else None
    if getattr(last_message, "tool_calls", None):
        return "research_tools"
    return "framework_analyst"


def create_nodes(llm: BaseChatModel, search_tool) -> GraphNodes:
    input_check_model = llm.with_structured_output(InputCheckResult)
    client_context_model = llm.with_structured_output(ClientContextResult)
    research_tool_model = llm.bind_tools([search_tool])
    research_result_model = llm.with_structured_output(FrameworkResearchResult)
    framework_analyst_model = llm.with_structured_output(FrameworkProfilesResult)
    comparison_model = llm.with_structured_output(FrameworkComparison)

    def input_check_node(state: AgentBridgeState) -> dict[str, Any]:
        user_input = get_user_question(state) or ""
        platform_context = state.platform_description or ""

        while True:
            result = input_check_model.invoke(
                [
                    SystemMessage(content=INPUT_CHECK_SYSTEM_PROMPT),
                    HumanMessage(
                        content=(
                            f"User input:\n{user_input}\n\n"
                            f"Known platform context:\n{platform_context or '<none>'}\n\n"
                            f"Uploaded document ids: {state.uploaded_document_ids}"
                        )
                    ),
                ]
            )

            if result.can_continue:
                return {
                    "user_question": result.user_question or user_input,
                    "platform_description": result.platform_description or platform_context,
                    "input_check_passed": True,
                    "missing_items": [],
                    "clarification_questions": [],
                }

            questions = result.clarification_questions[:5] or [
                "Can you describe the client, tech stack, data sources, constraints, and target agent workflow?"
            ]
            human_answer = interrupt(
                {
                    "type": "input_check_missing_information",
                    "message": "I need more information before starting the analysis.",
                    "missing_items": result.missing_items,
                    "questions": questions,
                }
            )

            user_input = f"{user_input}\n\nUser clarification:\n{resume_value_to_text(human_answer)}"

    def client_context_extractor_node(state: AgentBridgeState) -> dict[str, Any]:
        result = client_context_model.invoke(
            [
                SystemMessage(content=CLIENT_CONTEXT_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Framework question:\n{state.user_question or get_user_question(state) or ''}\n\n"
                        f"Client/platform context:\n{state.platform_description or '<none>'}\n\n"
                        f"Uploaded document ids: {state.uploaded_document_ids}"
                    )
                ),
            ]
        )
        return {"client_context": result.model_dump()}

    def framework_research_node(state: AgentBridgeState) -> dict[str, Any]:
        tool_outputs = get_search_tool_outputs(state.messages)[-MAX_SEARCH_CALLS:]
        if not tool_outputs:
            tool_request = research_tool_model.invoke(
                [
                    SystemMessage(content=RESEARCH_TOOL_SYSTEM_PROMPT),
                    HumanMessage(
                        content=(
                            f"Client context:\n{as_compact_json(state.client_context or {})}\n\n"
                            "Call search_web with the queries you need. Use at most 2 calls."
                        )
                    ),
                ]
            )
            tool_request = AIMessage(content=tool_request.content, tool_calls=(tool_request.tool_calls or [])[:MAX_SEARCH_CALLS])
            return {"messages": [tool_request]}

        research_result = research_result_model.invoke(
            [
                SystemMessage(content=RESEARCH_FACT_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Client context:\n{as_compact_json(state.client_context or {})}\n\n"
                        f"search_web tool outputs:\n{as_compact_json(tool_outputs)}"
                    )
                ),
            ]
        )

        return {
            "research_queries": research_result.research_queries[:MAX_SEARCH_CALLS],
            "research_sources": dedupe_sources([source.model_dump() for source in research_result.sources]),
            "raw_framework_facts": [fact.model_dump() for fact in research_result.raw_framework_facts],
        }

    def framework_analyst_node(state: AgentBridgeState) -> dict[str, Any]:
        result = framework_analyst_model.invoke(
            [
                SystemMessage(content=FRAMEWORK_ANALYST_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Client context:\n{as_compact_json(state.client_context or {})}\n\n"
                        f"Research sources:\n{as_compact_json(state.research_sources)}\n\n"
                        f"Raw framework facts:\n{as_compact_json(state.raw_framework_facts)}"
                    )
                ),
            ]
        )
        return {"framework_profiles": [profile.model_dump() for profile in result.framework_profiles]}

    def comparison_node(state: AgentBridgeState) -> dict[str, Any]:
        result = comparison_model.invoke(
            [
                SystemMessage(content=COMPARISON_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Client context:\n{as_compact_json(state.client_context or {})}\n\n"
                        f"Framework profiles:\n{as_compact_json(state.framework_profiles)}\n\n"
                        f"Sources:\n{as_compact_json(state.research_sources)}"
                    )
                ),
            ]
        )
        return {"framework_comparison": result.model_dump()}

    def recommendation_writer_node(state: AgentBridgeState) -> dict[str, Any]:
        response = llm.invoke(
            [
                SystemMessage(content=RECOMMENDATION_WRITER_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Client context:\n{as_compact_json(state.client_context or {})}\n\n"
                        f"Research sources:\n{as_compact_json(state.research_sources)}\n\n"
                        f"Framework profiles:\n{as_compact_json(state.framework_profiles)}\n\n"
                        f"Comparison result:\n{as_compact_json(state.framework_comparison or {})}"
                    )
                ),
            ]
        )

        return {
            "final_recommendation": response.content,
            "final_answer": response.content,
            "messages": [AIMessage(content=response.content)],
        }

    return GraphNodes(
        input_check=input_check_node,
        client_context_extractor=client_context_extractor_node,
        framework_research=framework_research_node,
        framework_analyst=framework_analyst_node,
        comparison=comparison_node,
        recommendation_writer=recommendation_writer_node,
    )
