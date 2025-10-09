from typing import Any, Dict, List

from src.google_grounding import search_google_grounding


class _StubTools:
    def __init__(self, results: List[dict[str, str]]):
        self.calls: List[Dict[str, Any]] = []
        self._results = results

    def googleSearch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(payload)
        return {
            "groundingMetadata": {
                "groundingChunks": [
                    {"web": result} for result in self._results
                ],
            }
        }


class _StubClient:
    def __init__(self, results: List[dict[str, str]]):
        self.tools = _StubTools(results)


def test_search_google_grounding_collects_references():
    captured: List[str] = []

    def logger(message: str) -> None:
        captured.append(message)

    references = [
        {"uri": "https://example.com", "title": "Example", "snippet": "Summary"}
    ]

    client = _StubClient(references)

    def factory() -> _StubClient:
        return client

    strategy = {"strategy_name": "Alpha", "rationale": "Test rationale"}

    results = search_google_grounding(
        strategy,
        factory,
        logger=logger,
    )

    assert results == references
    assert client.tools.calls and client.tools.calls[0]["query"].startswith("Alpha")
    assert captured == []


def test_search_google_grounding_handles_factory_failure():
    messages: List[str] = []

    def logger(message: str) -> None:
        messages.append(message)

    def factory() -> None:
        raise RuntimeError("no sdk")

    result = search_google_grounding({}, factory, logger=logger)

    assert result == []
    assert any("Unable to construct" in message for message in messages)


def test_search_google_grounding_mock_mode_logs_warning():
    warnings: List[str] = []

    def logger(message: str) -> None:
        warnings.append(message)

    client = _StubClient([])

    def factory() -> _StubClient:
        return client

    result = search_google_grounding(
        {"strategy_name": "Alpha"},
        factory,
        logger=logger,
        use_mock=True,
    )

    assert result == []
    assert warnings and "Skipping" in warnings[0]
