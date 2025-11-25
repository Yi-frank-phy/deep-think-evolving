"""Create a human-readable acceptance summary from spec-formatted logs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

SPEC_PATTERN = re.compile(r"\[Spec-(?P<tag>[A-Z0-9_-]+)\]\s*(?P<message>.*)")


def _normalise_task_status(status: str, overall_status: str) -> str:
    if status in {"pass", "fail"}:
        return status
    if overall_status == "fail":
        return "unknown"
    return "pass"


def generate_acceptance_report(log_lines: Iterable[str]) -> Dict[str, Any]:
    """Convert spec log lines into a structured acceptance summary."""

    tasks: List[Dict[str, Any]] = []
    files: List[str] = []
    events: List[Dict[str, str]] = []
    overall_status = "pass"
    current_task: Dict[str, Any] | None = None

    for raw_line in log_lines:
        match = SPEC_PATTERN.search(raw_line)
        if not match:
            continue

        tag = match.group("tag").upper()
        message = match.group("message").strip()
        events.append({"tag": tag, "message": message})

        if tag == "STEP":
            current_task = {"name": message or "Unnamed step", "status": "pending", "details": []}
            tasks.append(current_task)
            continue

        if tag == "OK":
            if current_task is None:
                current_task = {"name": message or "Completion", "status": "pass", "details": []}
                tasks.append(current_task)
            current_task["status"] = "pass"
            if message:
                current_task.setdefault("details", []).append(message)
            continue

        if tag == "ERR":
            overall_status = "fail"
            if current_task is None:
                current_task = {"name": message or "Failure", "status": "fail", "details": []}
                tasks.append(current_task)
            current_task["status"] = "fail"
            if message:
                current_task.setdefault("details", []).append(message)
            continue

        if tag == "FILE" and message:
            files.append(message)

        if current_task is not None and message:
            current_task.setdefault("details", []).append(f"{tag}: {message}")

    deduped_files = sorted(dict.fromkeys(files))
    for task in tasks:
        task["status"] = _normalise_task_status(task.get("status", "pending"), overall_status)

    return {
        "overall_status": overall_status,
        "tasks": tasks,
        "files": deduped_files,
        "events": events,
    }


def _format_text_report(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("Acceptance Summary")
    lines.append("==================")
    lines.append(f"Overall Status: {report['overall_status'].upper()}")

    if report["tasks"]:
        lines.append("\nTasks:")
        for task in report["tasks"]:
            lines.append(f" - [{task['status'].upper()}] {task['name']}")
            for detail in task.get("details", []):
                lines.append(f"     • {detail}")

    if report["files"]:
        lines.append("\nKey Files:")
        for file_path in report["files"]:
            lines.append(f" - {file_path}")

    return "\n".join(lines)


def _read_log_lines(path: Path | None) -> List[str]:
    if path is None or str(path) == "-":
        return sys.stdin.read().splitlines()

    log_path = Path(path)
    try:
        return log_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Log file not found: {log_path}") from exc


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log-file",
        type=Path,
        required=True,
        help="Path to the spec-formatted log file produced by main.py.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the acceptance report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        log_lines = _read_log_lines(args.log_file)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    report = generate_acceptance_report(log_lines)

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_format_text_report(report))

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

