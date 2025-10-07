import json

from fastapi.testclient import TestClient

import server


def test_websocket_snapshot_and_updates(tmp_path, monkeypatch):
    knowledge_dir = tmp_path / "knowledge_base"
    knowledge_dir.mkdir()

    monkeypatch.setattr(server, "KNOWLEDGE_BASE_DIR", knowledge_dir)
    monkeypatch.setattr(server, "POLL_INTERVAL_SECONDS", 0.01)

    def _list_files():
        return sorted(knowledge_dir.glob("*.json"))

    monkeypatch.setattr(server, "_list_reflection_files", _list_files)

    first_path = knowledge_dir / "alpha.json"
    first_payload = {
        "id": "alpha",
        "thread_id": "alpha",
        "thread_label": "Alpha",
        "outcome": "success",
        "reflection": "ok",
        "embedding": [0.1, 0.2],
    }
    first_path.write_text(json.dumps(first_payload), encoding="utf-8")

    client = TestClient(server.app)
    with client.websocket_connect("/ws/knowledge_base") as websocket:
        snapshot = websocket.receive_json()
        assert snapshot["type"] == "snapshot"
        assert snapshot["data"][0]["id"] == "alpha"

        updated_payload = first_payload | {"reflection": "updated"}
        first_path.write_text(json.dumps(updated_payload), encoding="utf-8")
        update_event = websocket.receive_json()
        assert update_event["type"] == "update"
        assert update_event["data"]["reflection"] == "updated"

        first_path.unlink()
        delete_event = websocket.receive_json()
        assert delete_event["type"] == "delete"
        assert delete_event["data"]["id"] == "alpha"
