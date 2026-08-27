from agentbridge.source_urls import normalize_source_url


def test_normalize_source_url_removes_tracking_details_and_fragment():
    assert (
        normalize_source_url(
            " HTTPS://Docs.Example.com/framework/?utm_source=search&version=2#installation "
        )
        == "https://docs.example.com/framework?version=2"
    )
