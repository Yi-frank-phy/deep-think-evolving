from src.google_grounding import search_google_grounding


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.prompts = []

    def generate_content(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.response


def test_search_google_grounding_success():
    response = {
        "grounding_metadata": {
            "grounding_chunks": [
                {
                    "web": {
                        "uri": "https://example.com/article",
                        "title": "Example Article",
                    },
                    "text": "A helpful snippet",
                },
                {
                    "web": {
                        "displayUrl": "https://example.org",
                        "title": "Second Result",
                    },
                    "text": "Another snippet",
                },
            ]
        }
    }

    fake_client = FakeClient(response=response)

    def factory():
        return fake_client

    result = search_google_grounding("quantum computing", client_factory=factory, max_results=1)

    assert result["query"] == "quantum computing"
    assert result["error"] is None
    assert len(result["results"]) == 1
    first = result["results"][0]
    assert first == {
        "url": "https://example.com/article",
        "title": "Example Article",
        "snippet": "A helpful snippet",
    }
    assert fake_client.prompts == ["quantum computing"]


def test_search_google_grounding_translates_exception():
    fake_client = FakeClient(error=RuntimeError("Boom"))

    def factory():
        return fake_client

    result = search_google_grounding("failing query", client_factory=factory)

    assert result["results"] == []
    assert result["error"] == {"code": "API_ERROR", "message": "Boom"}


def test_search_google_grounding_empty_chunks():
    response = {"grounding_metadata": {"grounding_chunks": []}}
    fake_client = FakeClient(response=response)

    def factory():
        return fake_client

    result = search_google_grounding("no results", client_factory=factory)

    assert result["results"] == []
    assert result["error"] == {
        "code": "NO_RESULTS",
        "message": "Google Grounding returned no grounding chunks.",
    }
