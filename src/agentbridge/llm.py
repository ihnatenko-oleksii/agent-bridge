"""LLM factory."""

from langchain_openai import ChatOpenAI

from agentbridge.config import DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS


def build_llm(*, model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT_SECONDS, max_retries: int = 0) -> ChatOpenAI:
    return ChatOpenAI(model=model, timeout=timeout, max_retries=max_retries)
