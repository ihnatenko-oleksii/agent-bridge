from agentbridge import config


def test_get_project_root_points_to_repo():
    assert config.get_project_root().name == "AgentBridge"


def test_validate_runtime_settings_without_langsmith_requirement():
    settings = config.Settings(
        openai_api_key="openai",
        serper_api_key="serper",
        langsmith_api_key=None,
        langsmith_tracing=None,
    )

    validated = config.validate_runtime_settings(settings, require_langsmith=False)
    assert validated is settings
