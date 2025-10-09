from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.generate_acceptance_report import (
    DEFAULT_LOG_PATH,
    generate_acceptance_report,
    main,
    render_markdown,
    summarise_log,
)


def test_generate_acceptance_report_succeeds(tmp_path: Path):
    log_path = tmp_path / "pipeline.log"
    log_content = "\n".join(
        [
            "[Spec-OK] --- Running Full Pipeline Test Script (Gemini + Ollama) ---",
            "[Spec-OK] [SUCCESS] Generated strategies",
            "[Spec-OK] --- Pipeline Execution Completed ---",
        ]
    )
    log_path.write_text(log_content, encoding="utf-8")

    summary, markdown = generate_acceptance_report(log_path)

    assert summary["prefixed_event_count"] == 3
    assert summary["status"] == "success"
    assert "### 成功事件" in markdown
    assert "未检测到失败事件" in markdown


def test_main_handles_missing_log(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    missing_path = tmp_path / "absent.log"

    exit_code = main(["--log-path", str(missing_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "未找到日志文件" in captured.out


def test_render_markdown_includes_failures():
    content = "\n".join(
        [
            "[Spec-OK] [FAILURE] Something broke",
            "[Spec-OK] --- Pipeline Execution Completed ---",
        ]
    )
    summary = summarise_log(content, log_path=DEFAULT_LOG_PATH)
    markdown = render_markdown(summary)

    assert "需关注" in markdown
    assert "失败/错误事件" in markdown


def test_generate_acceptance_report_outputs_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    log_path = tmp_path / "pipeline.log"
    log_path.write_text("[Spec-OK] --- Pipeline Execution Completed ---", encoding="utf-8")

    exit_code = main(["--log-path", str(log_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    json_blob = captured.out.split("\n--- Markdown", 1)[0]
    payload = json.loads(json_blob)
    assert payload["completed"] is True
