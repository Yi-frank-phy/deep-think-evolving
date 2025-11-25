import json

import requests

from src import embedding_client as ec


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(response=self)

    def json(self):
        return self._payload


def test_embed_text_success(monkeypatch):
    def fake_post(url, headers=None, data=None, json=None, **kwargs):
        if json:
            body = json
        elif data:
            import json as j
            body = j.loads(data)
        else:
            body = {}
            
        assert body["prompt"] == "hello"
        return DummyResponse({"embedding": [0.1, 0.2, 0.3]})

    monkeypatch.setattr(ec.requests, "post", fake_post)

    vector = ec.embed_text("hello")
    assert vector == [0.1, 0.2, 0.3]


def test_embed_text_handles_connection_error(monkeypatch):
    def fake_post(*_, **__):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(ec.requests, "post", fake_post)

    vector = ec.embed_text("hello")
    assert vector == []


def test_embed_strategies_handles_http_error(monkeypatch):
    def fake_post(url, headers=None, data=None, json=None, **kwargs):
        return DummyResponse({}, status_code=500)

    monkeypatch.setattr(ec.requests, "post", fake_post)

    strategies = [{"strategy_name": "A", "rationale": "", "initial_assumption": ""}]
    result = ec.embed_strategies(strategies)
    assert result[0]["embedding"] == []
