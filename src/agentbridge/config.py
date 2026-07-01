"""Configuration and environment helpers for AgentBridge."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

AGENT_NAME = "Framework Chooser"
DEFAULT_MODEL = "gpt-5.4-nano"
MAX_SEARCH_CALLS = 2
MAX_SOURCES = 8
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_RECURSION_LIMIT = 12


@dataclass(slots=True)
class Settings:
    openai_api_key: str | None = None
    serper_api_key: str | None = None
    langsmith_api_key: str | None = None
    langsmith_tracing: str | None = None
    langsmith_project: str | None = None
    langsmith_endpoint: str | None = None


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_project_dotenv(override: bool = True) -> str | None:
    dotenv_path = find_dotenv(filename=".env", usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path, override=override)
        refresh_langsmith_env_cache()
        return dotenv_path

    repo_dotenv = get_project_root() / ".env"
    if repo_dotenv.exists():
        load_dotenv(dotenv_path=repo_dotenv, override=override)
        refresh_langsmith_env_cache()
        return str(repo_dotenv)

    return None


def refresh_langsmith_env_cache() -> None:
    try:
        from langsmith.utils import get_env_var, get_tracer_project

        get_env_var.cache_clear()
        get_tracer_project.cache_clear()
    except Exception:
        pass


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        serper_api_key=os.getenv("SERPER_API_KEY"),
        langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
        langsmith_tracing=os.getenv("LANGSMITH_TRACING"),
        langsmith_project=os.getenv("LANGSMITH_PROJECT"),
        langsmith_endpoint=os.getenv("LANGSMITH_ENDPOINT"),
    )


def validate_runtime_settings(settings: Settings | None = None, *, require_langsmith: bool = True) -> Settings:
    settings = settings or get_settings()

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for live graph execution.")
    if not settings.serper_api_key:
        raise RuntimeError("SERPER_API_KEY is required for live framework research.")

    if require_langsmith:
        if not settings.langsmith_api_key:
            raise RuntimeError("LANGSMITH_API_KEY missing after load_project_dotenv.")
        if (settings.langsmith_tracing or "").lower() != "true":
            raise RuntimeError("Set LANGSMITH_TRACING=true in .env.")

    return settings
