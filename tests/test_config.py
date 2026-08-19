from agentbridge import config


def test_get_project_root_points_to_repo():
    assert (config.get_project_root() / "pyproject.toml").is_file()


def test_validate_runtime_settings_without_langsmith_requirement():
    settings = config.Settings(
        openai_api_key="openai",
        serper_api_key="serper",
        langsmith_api_key=None,
        langsmith_tracing=None,
    )

    validated = config.validate_runtime_settings(settings, require_langsmith=False)
    assert validated is settings


def test_validate_runtime_settings_lists_actionable_missing_key():
    settings = config.Settings(serper_api_key="serper")

    try:
        config.validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "Copy .env.example to .env" in str(exc)
    else:
        raise AssertionError("missing OpenAI key should fail")
