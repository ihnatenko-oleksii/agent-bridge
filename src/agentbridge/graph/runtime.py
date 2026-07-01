"""Runtime helpers for CLI, UI, and notebooks."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from agentbridge.config import get_settings, load_project_dotenv, validate_runtime_settings
from agentbridge.graph.builder import build_graph
from agentbridge.graph.helpers import format_graph_result, get_interrupt_payload, make_graph_config
from agentbridge.schemas import AgentBridgeState


@lru_cache(maxsize=1)
def get_runtime_graph():
    return build_graph()


def prepare_runtime(*, require_langsmith: bool = True):
    load_project_dotenv()
    validate_runtime_settings(get_settings(), require_langsmith=require_langsmith)
    return get_runtime_graph()


def run_recommendation(
    user_input: str,
    *,
    thread_id: str | None = None,
    platform_description: str | None = None,
    uploaded_document_ids: list[str] | None = None,
    require_langsmith: bool = True,
) -> dict[str, Any]:
    graph = prepare_runtime(require_langsmith=require_langsmith)
    state = AgentBridgeState(
        messages=[HumanMessage(content=user_input)],
        user_question=user_input,
        platform_description=platform_description,
        uploaded_document_ids=uploaded_document_ids or [],
    )
    return graph.invoke(state, config=make_graph_config(thread_id))


def resume_recommendation(answer: str, *, thread_id: str, require_langsmith: bool = True) -> dict[str, Any]:
    graph = prepare_runtime(require_langsmith=require_langsmith)
    return graph.invoke(Command(resume=answer), config=make_graph_config(thread_id))


def format_response(result: dict[str, Any]) -> str:
    return format_graph_result(result)


def get_pending_interrupt(result: dict[str, Any]) -> dict[str, Any] | None:
    return get_interrupt_payload(result)


def flush_langsmith_traces() -> None:
    try:
        from langsmith import Client

        client = Client()
        if hasattr(client, "flush"):
            client.flush()
    except Exception:
        pass
