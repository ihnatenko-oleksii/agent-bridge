from types import SimpleNamespace

from agentbridge import cli


def test_run_cli_session_resumes_clarification_on_the_same_thread(monkeypatch):
    results = iter(
        [
            {
                "__interrupt__": [
                    SimpleNamespace(value={"message": "Need context", "questions": ["What stack?"]})
                ]
            },
            {"final_recommendation": "Use LangGraph"},
        ]
    )
    calls = []

    def fake_run(question, **kwargs):
        calls.append(("run", question, kwargs))
        return next(results)

    def fake_resume(answer, **kwargs):
        calls.append(("resume", answer, kwargs))
        return next(results)

    monkeypatch.setattr(cli, "run_recommendation", fake_run)
    monkeypatch.setattr(cli, "resume_recommendation", fake_resume)

    displayed = []
    prompts = []
    response = cli.run_cli_session(
        "Choose a framework",
        input_fn=lambda prompt: prompts.append(prompt) or "Python on AWS",
        output_fn=displayed.append,
    )

    assert response == "Use LangGraph"
    assert displayed == ["Need context\n\n- What stack?"]
    assert prompts == ["Clarification: "]
    assert calls[0][0] == "run"
    assert calls[1] == ("resume", "Python on AWS", {"thread_id": calls[0][2]["thread_id"], "require_langsmith": False})


def test_run_cli_session_non_interactive_returns_pending_prompt(monkeypatch):
    pending_result = {
        "__interrupt__": [SimpleNamespace(value={"message": "Need context", "questions": ["What stack?"]})]
    }
    monkeypatch.setattr(cli, "run_recommendation", lambda *args, **kwargs: pending_result)

    response = cli.run_cli_session(
        "Choose a framework",
        interactive=False,
        input_fn=lambda _: (_ for _ in ()).throw(AssertionError("input should not be read")),
    )

    assert response == "Need context\n\n- What stack?"
