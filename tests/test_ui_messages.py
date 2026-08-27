from agentbridge.ui.messages import format_runtime_error


def test_format_runtime_error_is_safe_for_chat_output():
    message = format_runtime_error()

    assert message == "AgentBridge could not complete the request. Check your configuration and try again."
