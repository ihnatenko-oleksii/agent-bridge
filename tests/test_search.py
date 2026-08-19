from agentbridge.tools.search import build_search_tool, classify_source, normalize_search_results


class FakeSearchClient:
    def __init__(self, payload, k=5):
        self.payload = payload
        self.k = k

    def results(self, query: str):
        return self.payload


def test_classify_source_urls():
    assert classify_source("https://github.com/langchain-ai/langgraph") == ("github", "high")
    assert classify_source("https://docs.langchain.com/oss/python/langgraph") == ("official_docs", "high")
    assert classify_source("https://medium.com/@example/frameworks") == ("technical_blog", "medium")


def test_normalize_search_results():
    payload = {
        "organic": [
            {
                "title": "LangGraph Docs",
                "link": "https://docs.langchain.com/oss/python/langgraph",
                "snippet": "Official docs\nwith newline",
            }
        ]
    }

    normalized = normalize_search_results(payload, limit=5)
    assert normalized == [
        {
            "title": "LangGraph Docs",
            "url": "https://docs.langchain.com/oss/python/langgraph",
            "summary": "Official docs with newline",
            "source_type": "official_docs",
            "reliability": "high",
        }
    ]


def test_normalize_search_results_ignores_malformed_payloads():
    assert normalize_search_results(None, limit=5) == []
    assert normalize_search_results({"organic": "not-a-list"}, limit=5) == []
    assert normalize_search_results({"organic": [None, {"link": "javascript:alert(1)"}]}, limit=5) == []


def test_build_search_tool_formats_results():
    payload = {
        "organic": [
            {
                "title": "Release Notes",
                "link": "https://example.com/changelog",
                "snippet": "Recent changes",
            }
        ]
    }
    tool = build_search_tool(search_client=FakeSearchClient(payload))

    response = tool.invoke({"query": "agent frameworks"})
    assert "Query: agent frameworks" in response
    assert "Release Notes" in response


def test_search_tool_turns_provider_failure_into_model_visible_result():
    class BrokenClient:
        k = 5

        def results(self, query):
            raise TimeoutError("secret provider details")

    response = build_search_tool(search_client=BrokenClient()).invoke({"query": "agent frameworks"})
    assert response == '{"query": "agent frameworks", "error": "Search provider failed: TimeoutError"}'
