import json
from pathlib import Path

import pytest

from src import context_manager as cm


def _configure_temp_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context_root = tmp_path / "runtime_contexts"
    knowledge_root = tmp_path / "knowledge_base"
    monkeypatch.setattr(cm, "CONTEXT_ROOT", context_root)
    monkeypatch.setattr(cm, "KNOWLEDGE_BASE_ROOT", knowledge_root)


def test_context_creation_and_summary_fallback(tmp_path, monkeypatch):
    _configure_temp_roots(tmp_path, monkeypatch)

    thread_id = "Alpha Strategy"
    context_path = cm.create_context(thread_id)
    assert context_path.exists()
    prompt_path = context_path / "prompt.md"
    history_path = context_path / "history.log"
    assert prompt_path.exists()
    assert history_path.exists()

    cm.append_step(thread_id, {"event": "init", "payload": 1})

    summary = cm.generate_summary(thread_id)
    assert summary.path.exists()
    assert "Fallback" in summary.text


def test_record_reflection_persists_payload(tmp_path, monkeypatch):
    _configure_temp_roots(tmp_path, monkeypatch)
    monkeypatch.setattr(cm, "embed_text", lambda _: [0.1, 0.2, 0.3])

    thread_id = "Beta"
    cm.create_context(thread_id)
    cm.append_step(thread_id, {"event": "planning"})

    reflection_path = cm.record_reflection(
        thread_id,
        "Reflection details",
        outcome="success",
        metadata={"score": 0.95},
    )

    payload = json.loads(reflection_path.read_text(encoding="utf-8"))
    assert payload["thread_label"] == thread_id
    assert payload["embedding"] == [0.1, 0.2, 0.3]
    assert payload["source"]["metadata"] == {"score": 0.95}
