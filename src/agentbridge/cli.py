"""CLI entry point."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from uuid import uuid4

from agentbridge.graph.runtime import (
    format_response,
    get_pending_interrupt,
    resume_recommendation,
    run_recommendation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AgentBridge from the command line.")
    parser.add_argument("question", help="Framework-selection question to evaluate.")
    parser.add_argument("--thread-id", dest="thread_id", default=None, help="Optional LangGraph thread id.")
    parser.add_argument(
        "--require-langsmith",
        action="store_true",
        help="Require LangSmith tracing configuration (optional by default).",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Print clarification requests without waiting for terminal input.",
    )
    return parser


def run_cli_session(
    question: str,
    *,
    thread_id: str | None = None,
    require_langsmith: bool = False,
    interactive: bool = True,
    input_fn: Callable[[str], str] | None = None,
    output_fn: Callable[[str], None] | None = None,
) -> str:
    """Run a recommendation and optionally answer checkpointed clarifications."""
    input_fn = input_fn or input
    output_fn = output_fn or print
    session_thread_id = thread_id or f"agentbridge-cli-{uuid4().hex}"
    result = run_recommendation(
        question,
        thread_id=session_thread_id,
        require_langsmith=require_langsmith,
    )

    while interactive and get_pending_interrupt(result):
        output_fn(format_response(result))
        answer = input_fn("Clarification: ")
        if not answer.strip():
            raise RuntimeError("Clarification answer cannot be empty.")
        result = resume_recommendation(
            answer,
            thread_id=session_thread_id,
            require_langsmith=require_langsmith,
        )

    return format_response(result)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        response = run_cli_session(
            args.question,
            thread_id=args.thread_id,
            require_langsmith=args.require_langsmith,
            interactive=not args.non_interactive,
        )
    except (RuntimeError, EOFError) as exc:
        parser.error(str(exc))
    print(response)


if __name__ == "__main__":
    main()
