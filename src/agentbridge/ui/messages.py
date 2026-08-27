"""Stable, non-sensitive messages exposed by the AgentBridge UI."""

from __future__ import annotations


def format_runtime_error() -> str:
    """Return a user-facing error without exposing provider exception details."""
    return "AgentBridge could not complete the request. Check your configuration and try again."
