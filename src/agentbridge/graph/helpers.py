"""Pure helpers for graph execution and display."""

from __future__ import annotations

import json
import uuid
from typing import Any

from agentbridge.config import DEFAULT_RECURSION_LIMIT, MAX_SOURCES


def get_user_question(state) -> str | None:
    if state.user_question:
        return state.user_question

    for message in reversed(state.messages):
        role = getattr(message, "type", None) or getattr(message, "role", None)
        if role in {"human", "user"}:
            return message.content

    return None


def make_graph_config(thread_id: str | None = None) -> dict[str, Any]:
    return {
        "configurable": {"thread_id": thread_id or f"agentbridge-{uuid.uuid4().hex}"},
        "recursion_limit": DEFAULT_RECURSION_LIMIT,
    }


def get_interrupt_payload(result: dict[str, Any]) -> dict[str, Any] | None:
    interrupts = result.get("__interrupt__") or []
    if not interrupts:
        return None
    return interrupts[0].value


def format_interrupt_payload(payload: dict[str, Any]) -> str:
    questions = payload.get("questions") or payload.get("clarification_questions") or []
    question_block = "\n".join(f"- {question}" for question in questions)
    return f"{payload.get('message', 'I need more information.')}\n\n{question_block}".strip()


def format_graph_result(result: dict[str, Any]) -> str:
    payload = get_interrupt_payload(result)
    if payload:
        return format_interrupt_payload(payload)
    if result.get("final_recommendation"):
        return result["final_recommendation"]
    if result.get("final_answer"):
        return result["final_answer"]
    messages = result.get("messages") or []
    if messages:
        return messages[-1].content
    return "The graph finished without producing a message."


def resume_value_to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "\n".join(f"{key}: {val}" for key, val in value.items())
    return str(value)


def as_compact_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def dedupe_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []
    for source in sources:
        url = source.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(source)
    return deduped[:MAX_SOURCES]


def get_search_tool_outputs(messages: list[Any]) -> list[dict[str, str]]:
    tool_queries_by_id = {}
    outputs = []

    for message in messages:
        for tool_call in getattr(message, "tool_calls", []) or []:
            if tool_call.get("name") == "search_web":
                tool_queries_by_id[tool_call.get("id")] = (tool_call.get("args") or {}).get("query", "")

        if getattr(message, "type", None) == "tool" and getattr(message, "name", None) == "search_web":
            outputs.append(
                {
                    "query": tool_queries_by_id.get(getattr(message, "tool_call_id", None), ""),
                    "output": message.content,
                }
            )

    return outputs


def pretty_print_state_keys(state: dict[str, Any]) -> None:
    for key in [
        "input_check_passed",
        "missing_items",
        "clarification_questions",
        "client_context",
        "research_queries",
        "research_sources",
        "framework_profiles",
        "framework_comparison",
    ]:
        print(f"{key}: {state.get(key)}")


def print_sources(state: dict[str, Any]) -> None:
    for source in state.get("research_sources", []):
        print(f"- {source.get('title')} -> {source.get('url')}")
