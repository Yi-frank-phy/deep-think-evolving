import json
from pathlib import Path

import pytest

from src import context_manager as cm


def _configure_temp_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context_root = tmp_path / "runtime_contexts"
    knowledge_root = tmp_path / "knowledge_base"
    monkeypatch.setattr(cm, "CONTEXT_ROOT", context_root)
    monkeypatch.setattr(cm, "KNOWLEDGE_BASE_ROOT", knowledge_root)
    monkeypatch.delenv(cm.HISTORY_LIMIT_ENV_VAR, raising=False)


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


def test_append_step_enforces_history_limit(tmp_path, monkeypatch):
    _configure_temp_roots(tmp_path, monkeypatch)

    thread_id = "Gamma"
    cm.create_context(thread_id)

    limit = cm.get_history_limit()
    total_entries = limit + 5
    for index in range(total_entries):
        cm.append_step(thread_id, {"index": index})

    history_path = cm.CONTEXT_ROOT / cm._sanitize_thread_id(thread_id) / "history.log"
    lines = [line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(lines) == limit
    first_entry = json.loads(lines[0])
    assert first_entry["data"]["index"] == total_entries - limit


def test_append_step_respects_custom_history_limit(tmp_path, monkeypatch):
    _configure_temp_roots(tmp_path, monkeypatch)

    custom_limit = 5
    monkeypatch.setenv(cm.HISTORY_LIMIT_ENV_VAR, str(custom_limit))

    thread_id = "Custom"
    cm.create_context(thread_id)

    for index in range(custom_limit + 3):
        cm.append_step(thread_id, {"index": index})

    history_path = cm.CONTEXT_ROOT / cm._sanitize_thread_id(thread_id) / "history.log"
    lines = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(lines) == custom_limit
    assert lines[0]["data"]["index"] == 3
