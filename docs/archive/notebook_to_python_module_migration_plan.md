# Notebook to Python Module Migration Plan

Created: 2026-06-21

## Goal

Migrate `experiment_langgraph_one_agent.ipynb` from a single exploratory notebook into a maintainable Python module/package while preserving the notebook as a lightweight demo or scratchpad.

The target result is a reusable `agentbridge` Python package with:

- clear module boundaries for prompts, schemas, tools, graph nodes, graph assembly, runtime helpers, and UI
- repeatable local commands using the existing `uv` and `pyproject.toml` setup
- tests for deterministic code and thin smoke tests for LangGraph wiring
- optional notebook cells that import the package instead of defining the application inline

## Current Project Snapshot

Files currently present:

- `README.md`
- `pyproject.toml`
- `uv.lock`
- `experiment_langgraph_one_agent.ipynb`

Important current dependencies from `pyproject.toml`:

- Python `>=3.12`
- `langgraph`
- `langchain`
- `langchain-openai`
- `langchain-community`
- `langgraph-checkpoint-sqlite`
- `langsmith`
- `gradio`
- `python-dotenv`
- `jupyter` and `ipykernel`

The notebook currently contains:

- environment loading and LangSmith validation
- prompt constants
- `ChatOpenAI` setup
- Pydantic state and artifact schemas
- Serper-backed web search tool
- helper functions for graph config, interrupts, result formatting, JSON formatting, source dedupe, and state display
- LangGraph nodes for input checking, client context extraction, framework research, framework analysis, comparison, and recommendation writing
- graph construction and compilation with `MemorySaver`
- commented manual test examples
- Gradio chat UI

## Migration Principles

- Keep the notebook runnable during migration. Move code out one section at a time and replace notebook code with imports.
- Preserve behavior first. Refactor names and interfaces only after tests or smoke checks cover the current behavior.
- Keep LLM calls behind small functions/classes so graph assembly can be tested without calling remote models.
- Keep environment and runtime concerns separate from graph logic.
- Avoid hardcoding framework candidates; preserve the current source-backed research behavior.
- Make modules importable without requiring live API keys. Validate API keys only in runtime entry points.

## Target Layout

Use a `src/` layout so imports behave like an installed package:

```text
AgentBridge/
  pyproject.toml
  README.md
  docs/
    notebook_to_python_module_migration_plan.md
  notebooks/
    experiment_langgraph_one_agent.ipynb
  src/
    agentbridge/
      __init__.py
      config.py
      prompts.py
      schemas.py
      llm.py
      tools/
        __init__.py
        search.py
      graph/
        __init__.py
        helpers.py
        nodes.py
        builder.py
        runtime.py
      ui/
        __init__.py
        gradio_app.py
      cli.py
  tests/
    test_config.py
    test_search.py
    test_graph_helpers.py
    test_graph_builder.py
```

Proposed responsibilities:

- `config.py`: environment loading, settings model, LangSmith validation, app constants such as `MAX_SEARCH_CALLS` and `MAX_SOURCES`
- `prompts.py`: all system prompts as named constants
- `schemas.py`: Pydantic models for source items, framework facts, framework profiles, comparisons, state, and structured LLM outputs
- `llm.py`: model factory for `ChatOpenAI`
- `tools/search.py`: Serper wrapper, source classification, search result normalization, `search_web` tool
- `graph/helpers.py`: graph config, interrupt formatting, result formatting, source dedupe, compact JSON, state inspection helpers
- `graph/nodes.py`: node factory or node functions for input check, client context extraction, research, analysis, comparison, and recommendation writing
- `graph/builder.py`: graph construction and compilation
- `graph/runtime.py`: high-level invoke/resume helpers for CLI, UI, and notebook usage
- `ui/gradio_app.py`: Gradio Blocks app and launch function
- `cli.py`: optional command-line entry point for smoke testing and one-shot recommendations

## Notebook-to-Module Mapping

| Notebook section | Move to | Notes |
|---|---|---|
| Imports and env loading | `config.py`, module-specific imports | Do not validate API keys on plain package import. |
| Constants and system prompts | `prompts.py`, `config.py` | Keep prompts versionable and reviewable. |
| LLM definition | `llm.py` | Use a factory such as `build_llm(settings)`. |
| State schemas | `schemas.py` | Keep Pydantic models together initially. Split later only if they grow. |
| Search helpers and tool | `tools/search.py` | Add unit tests for source classification and output normalization. |
| Runtime helper functions | `graph/helpers.py` | Keep pure helpers easy to unit test. |
| LangGraph node functions | `graph/nodes.py` | Consider dependency injection for models and tools. |
| Graph assembly | `graph/builder.py` | Return a compiled graph from a single public function. |
| Manual examples | `tests/`, `notebooks/` | Convert deterministic parts to tests and keep examples in the notebook. |
| Gradio app | `ui/gradio_app.py` | Provide `create_app()` and `launch_app()`. |

## Phased Plan

### Phase 1: Prepare the package skeleton

- Create `src/agentbridge/` with subpackages for `tools`, `graph`, and `ui`.
- Move the notebook into `notebooks/` or keep it temporarily at the root until imports are stable.
- Update `pyproject.toml` with package metadata and development tooling.
- Add a minimal test setup.

Recommended `pyproject.toml` changes:

- Add a `[project.scripts]` table if one does not already exist.
- Merge new dev tools into the existing `[dependency-groups].dev` list. Do not create a second `[dependency-groups]` table.

```toml
[project.scripts]
agentbridge = "agentbridge.cli:main"

[dependency-groups]
dev = [
    "ipykernel>=6.29.5",
    "pytest>=8.0.0",
    "ruff>=0.8.0",
]
```

Initial verification:

```bash
uv run python -c "import agentbridge; print(agentbridge.__name__)"
uv run pytest
```

### Phase 2: Extract configuration and prompts

- Move `agent_name`, `MAX_SEARCH_CALLS`, and `MAX_SOURCES` into `config.py`.
- Move all system prompt strings into `prompts.py`.
- Add a settings object for environment-derived values:
  - `OPENAI_API_KEY`
  - `LANGSMITH_API_KEY`
  - `LANGSMITH_TRACING`
  - `LANGSMITH_PROJECT`
  - `LANGSMITH_ENDPOINT`
  - `SERPER_API_KEY`
- Ensure importing `agentbridge.prompts` or `agentbridge.schemas` does not require `.env` or external services.

Tests:

- settings loads defaults without touching network
- LangSmith validation fails with a clear message only when runtime validation is requested

### Phase 3: Extract schemas and pure helpers

- Move Pydantic models into `schemas.py`.
- Move pure helper functions into `graph/helpers.py`.
- Keep helpers free of LLM, Gradio, and network dependencies.

Priority tests:

- `resume_value_to_text()` formats strings, dicts, and other objects predictably
- `dedupe_sources()` removes duplicate URLs and respects `MAX_SOURCES`
- `format_interrupt_payload()` handles both `questions` and `clarification_questions`
- `format_graph_result()` prefers interrupts, then final recommendation, then final answer, then final message

### Phase 4: Extract search tool

- Move `classify_source()`, `_search_sources()`, and `search_web()` into `tools/search.py`.
- Wrap `GoogleSerperAPIWrapper` construction so tests can inject a fake search client.
- Keep source normalization deterministic.

Suggested API:

```python
def classify_source(url: str) -> tuple[str, str]:
    ...

def build_search_tool(search_client: SearchClient | None = None):
    ...
```

Tests:

- GitHub URLs classify as `github` and high reliability
- documentation URLs classify as `official_docs` and high reliability
- blog URLs classify as `technical_blog` and medium reliability
- fake search results are converted into `SourceItem` dictionaries

### Phase 5: Extract LLM and node construction

- Move the `ChatOpenAI` creation into `llm.py`.
- Move node functions into `graph/nodes.py`.
- Prefer a node factory that accepts dependencies:

```python
def create_nodes(llm: BaseChatModel, search_tool: BaseTool) -> GraphNodes:
    ...
```

This keeps tests from depending on the live OpenAI API.

Tests:

- node factory can be constructed with fake model/tool objects
- routing functions return the expected route names
- research node requests tools when no tool outputs are present
- research node converts fake tool outputs into research artifacts

### Phase 6: Extract graph builder and runtime API

- Move graph assembly into `graph/builder.py`.
- Keep checkpointer choice configurable:
  - `MemorySaver` for notebook and local demos
  - SQLite checkpointer later if persistence is needed
- Add `graph/runtime.py` with high-level functions:
  - `run_recommendation(user_input: str, thread_id: str | None = None)`
  - `resume_recommendation(thread_id: str, answer: str)`
  - `format_response(result: dict)`

Tests:

- graph builder registers expected node names
- graph compiles with fake dependencies
- one smoke test invokes a tiny graph path without remote services if feasible

### Phase 7: Extract Gradio UI

- Move Gradio code into `ui/gradio_app.py`.
- Split UI construction from launch:

```python
def create_app() -> gr.Blocks:
    ...

def launch_app() -> None:
    create_app().launch()
```

- Let the UI import `run_recommendation()` and `resume_recommendation()` from `graph/runtime.py`; do not introduce an app runtime class unless the implementation shows a concrete need.
- Keep `flush_langsmith_traces()` in runtime or UI only if it is UI-specific.
- Ensure the UI can be imported in tests without launching a server.

Verification:

```bash
uv run python -m agentbridge.ui.gradio_app
```

### Phase 8: Replace notebook implementation with imports

- Move the original notebook to `notebooks/experiment_langgraph_one_agent.ipynb`.
- Replace large code cells with small cells that import from `agentbridge`.
- Replace direct `load_dotenv(dotenv_path=".env")` usage with repo-root-aware loading, such as `find_dotenv(usecwd=True)` or a helper from `agentbridge.config`, so moving the notebook under `notebooks/` does not break environment loading.
- Keep notebook cells focused on:
  - loading `.env`
  - building the graph
  - rendering the graph diagram
  - running short manual examples
  - optionally launching the Gradio app

The notebook should become a consumer of the package, not the source of truth.

### Phase 9: Update documentation

- Update `README.md` with:
  - project purpose
  - setup commands
  - required environment variables
  - notebook usage
  - CLI usage
  - Gradio launch command
  - testing command
- Add a short architecture document if the module structure stabilizes:
  - `docs/architecture.md`

### Phase 10: Cleanup and hardening

- Remove duplicated code from the notebook after package imports work.
- Move Jupyter dependencies to the dev dependency group if the package runtime does not need them.
- Add linting/formatting with `ruff`.
- Add type checks later if useful.
- Decide whether `langgraph-checkpoint-sqlite` should replace in-memory checkpointing for the app.
- Add a small CI workflow once tests exist.

## Suggested Public APIs

Keep the package surface small:

```python
from agentbridge.graph.builder import build_graph
from agentbridge.graph.runtime import run_recommendation, resume_recommendation
from agentbridge.ui.gradio_app import create_app
```

Avoid exposing internal node functions as public API until they settle.

## Environment Variable Plan

Runtime entry points should load `.env` and validate required values. Library imports should not.

Required for full live runs:

- `OPENAI_API_KEY`
- `SERPER_API_KEY`
- `LANGSMITH_API_KEY`
- `LANGSMITH_TRACING=true`

Optional:

- `LANGSMITH_PROJECT`
- `LANGSMITH_ENDPOINT`

Failure mode:

- Missing live-run variables should raise a clear configuration error before graph execution starts.
- Unit tests should not require any of these variables.

## Testing Strategy

Use layers:

- Unit tests for pure helpers and schema behavior
- Unit tests with fake search clients for tool normalization
- Graph assembly tests with fake LLM/tool dependencies
- Optional integration tests for real LLM/search behind an explicit marker such as `integration`
- Manual notebook and Gradio smoke checks after core modules pass tests

Suggested commands:

```bash
uv run pytest
uv run ruff check .
uv run python -m agentbridge.cli "What AI agent framework should we use?"
uv run python -m agentbridge.ui.gradio_app
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Importing modules triggers `.env` validation or network calls | Tests and tooling become brittle | Validate only in runtime entry points. |
| Node functions remain tightly coupled to global `llm` and `search_web` | Hard to test or swap dependencies | Use factories or dependency injection. |
| Notebook and package diverge | Confusing source of truth | Notebook must import package code after migration. |
| LLM behavior changes during refactor | Subtle regressions | Preserve prompts, schemas, and routing first; refactor only after smoke checks. |
| Gradio app launches on import | Tests hang or local imports become unsafe | Use `create_app()` and protect launch with `if __name__ == "__main__"`. |
| API keys leak into tests or docs | Security issue | Use `.env.example`, never commit real secrets, and keep tests key-free. |

## Definition of Done

The migration is complete when:

- `uv run pytest` passes
- `uv run python -c "import agentbridge"` works
- the notebook imports package modules instead of defining the core graph inline
- the graph can be built from `agentbridge.graph.builder`
- the Gradio app can be launched from a module or script entry point
- README setup and run commands are accurate
- no runtime API key validation happens during simple package import

## Recommended Next Implementation Order

1. Add `src/agentbridge/` and basic tests.
2. Extract `prompts.py`, `schemas.py`, and `graph/helpers.py`.
3. Add tests for helpers and source classification.
4. Extract `tools/search.py`.
5. Extract `llm.py`, `graph/nodes.py`, and `graph/builder.py`.
6. Extract `ui/gradio_app.py`.
7. Convert notebook cells to imports.
8. Update README.

## Notes for Future Codex Sessions

When resuming this plan:

- Start by reading this file and the current `pyproject.toml`.
- Inspect the notebook before editing because it is currently the implementation source.
- Make one extraction phase at a time and run the smallest relevant verification after each phase.
- Do not remove the notebook until the package path is stable and documented.
