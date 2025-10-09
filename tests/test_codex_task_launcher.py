"""Tests for the Codex task materialisation utility."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.initiate_codex_tasks import TASK_REGISTRY, initiate_codex_tasks


@pytest.fixture()
def tmp_repo(tmp_path: Path) -> Path:
    """Provide a disposable repository root for task generation."""

    # Mimic repository layout expected by the script
    (tmp_path / "codex_tasks").mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_initiate_codex_tasks_creates_expected_files(tmp_repo: Path) -> None:
    created_paths = initiate_codex_tasks(base_dir=tmp_repo)

    assert len(created_paths) == len(TASK_REGISTRY)

    for path in created_paths:
        assert path.exists(), f"Expected task file {path} to be created"
        payload = json.loads(path.read_text(encoding="utf-8"))

        assert payload["task_id"].startswith("T-"), "Task identifiers should follow T-XXX format"
        assert payload["status"] == "ready"
        assert isinstance(payload["steps"], list) and payload["steps"], "Steps must be a non-empty list"
        assert any(
            "merge origin/main" in step for step in payload["steps"]
        ), "Steps should direct merging the latest main branch"
        assert "specify check" in payload["validation_commands"], "Validation commands should list specify check"


def test_initiate_codex_tasks_respects_no_force(tmp_repo: Path) -> None:
    first_run = initiate_codex_tasks(base_dir=tmp_repo)
    assert first_run

    # Modify one file to ensure it is preserved when force=False
    marker_path = first_run[0]
    marker_path.write_text("{}", encoding="utf-8")

    skipped = initiate_codex_tasks(base_dir=tmp_repo, force=False)
    assert skipped == []
    assert marker_path.read_text(encoding="utf-8") == "{}"
