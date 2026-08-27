from langchain_core.messages import HumanMessage

from agentbridge.graph import runtime


class RecordingGraph:
    def __init__(self):
        self.calls = []

    def invoke(self, state, config):
        self.calls.append((state, config))
        return {"final_recommendation": "Use the evaluated winner"}


def test_run_recommendation_builds_structured_initial_state(monkeypatch):
    graph = RecordingGraph()
    monkeypatch.setattr(runtime, "prepare_runtime", lambda **kwargs: graph)

    result = runtime.run_recommendation(
        "Choose a framework",
        thread_id="demo-thread",
        platform_description="Python on AWS",
        uploaded_document_ids=["architecture.md"],
    )

    state, config = graph.calls[0]
    assert result["final_recommendation"] == "Use the evaluated winner"
    assert state.user_question == "Choose a framework"
    assert state.platform_description == "Python on AWS"
    assert state.uploaded_document_ids == ["architecture.md"]
    assert isinstance(state.messages[0], HumanMessage)
    assert config["configurable"]["thread_id"] == "demo-thread"
