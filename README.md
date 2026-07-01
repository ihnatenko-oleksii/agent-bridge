# AgentBridge

LangGraph-based advisor that helps companies choose which AI agent or RAG framework to use or integrate into their existing platform.

It should analyze client documents, research current frameworks on the web, compare options against requirements, validate claims with sources, and produce a practical integration proposal.

**Status:** experimental — early exploration, now split into a reusable Python package plus a package-backed notebook for manual runs.

## Project layout

- `src/agentbridge/`: package source for prompts, schemas, graph assembly, runtime helpers, UI, and CLI
- `notebooks/experiment_langgraph_one_agent.ipynb`: package-backed notebook for manual exploration
- `tests/`: focused tests for helpers, search normalization, and graph wiring

## Local commands

```bash
uv run python -c "import agentbridge; print(agentbridge.__name__)"
uv run pytest
uv run agentbridge "What AI agent framework should we use?"
uv run python -m agentbridge.ui.gradio_app
```
