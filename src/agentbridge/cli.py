"""CLI entry point."""

from __future__ import annotations

import argparse

from agentbridge.graph.runtime import format_response, run_recommendation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AgentBridge from the command line.")
    parser.add_argument("question", help="Framework-selection question to evaluate.")
    parser.add_argument("--thread-id", dest="thread_id", default=None, help="Optional LangGraph thread id.")
    parser.add_argument(
        "--require-langsmith",
        action="store_true",
        help="Require LangSmith tracing configuration (optional by default).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        result = run_recommendation(args.question, thread_id=args.thread_id, require_langsmith=args.require_langsmith)
    except RuntimeError as exc:
        parser = build_parser()
        parser.error(str(exc))
    print(format_response(result))


if __name__ == "__main__":
    main()
