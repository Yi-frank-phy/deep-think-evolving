from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from scripts.generate_acceptance_report import (
    generate_acceptance_report,
    main,
)


def test_generate_acceptance_report_succeeds():
    log_lines = [
        "[Spec-OK] --- Running Full Pipeline Test Script (Gemini + Ollama) ---",
        "[Spec-OK] [SUCCESS] Generated strategies",
        "[Spec-OK] --- Pipeline Execution Completed ---",
    ]

    report = generate_acceptance_report(log_lines)

    assert report["overall_status"] == "pass"
    # The first OK tag creates the task. Subsequent OK tags add to details.
    assert any("Generated strategies" in str(task.get("details", [])) for task in report["tasks"])
    assert report["events"]  # Events are always collected
    # Wait, let's check the script logic.
    # OK tag -> current_task["status"] = "pass"
    # It doesn't add to events list unless it's a generic tag?
    # events.append({"tag": tag, "message": message}) happens for ALL matches.
    assert len(report["events"]) == 3


def test_main_handles_missing_log(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    missing_path = tmp_path / "absent.log"

    # The new main uses argparse and prints to stderr on error?
    # It calls _read_log_lines which raises FileNotFoundError.
    # main catches it and prints Error: ...
    
    exit_code = main(["--log-file", str(missing_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error:" in captured.err or "Error:" in captured.out


def test_generate_acceptance_report_outputs_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    log_path = tmp_path / "pipeline.log"
    log_path.write_text("[Spec-OK] --- Pipeline Execution Completed ---", encoding="utf-8")

    exit_code = main(["--log-file", str(log_path), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    json_blob = captured.out.strip()
    payload = json.loads(json_blob)
    assert payload["overall_status"] == "pass"
