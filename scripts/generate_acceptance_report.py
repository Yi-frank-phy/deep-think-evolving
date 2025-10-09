"""Generate Spec Kit acceptance report summaries from pipeline logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

SPEC_PREFIX = "[Spec-OK]"
DEFAULT_LOG_PATH = Path("logs/pipeline.log")


def read_log(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def _filter_prefixed_lines(lines: Iterable[str]) -> list[str]:
    return [line for line in lines if line.strip().startswith(SPEC_PREFIX)]


def summarise_log(content: str, *, log_path: Path) -> Dict[str, Any]:
    lines = content.splitlines()
    prefixed = _filter_prefixed_lines(lines)
    successes = [line for line in prefixed if "[SUCCESS]" in line]
    failures = [line for line in prefixed if "[FAILURE]" in line or "[ERROR]" in line]
    completion = any("Pipeline Execution Completed" in line for line in prefixed)

    return {
        "log_path": str(log_path),
        "total_lines": len(lines),
        "prefixed_event_count": len(prefixed),
        "success_events": successes,
        "failure_events": failures,
        "status": "success" if completion and not failures else "attention",
        "completed": completion,
    }


def render_markdown(summary: Dict[str, Any]) -> str:
    lines = ["## 验收摘要"]
    lines.append(f"- 日志路径：`{summary['log_path']}`")
    lines.append(f"- 总行数：{summary['total_lines']}")
    lines.append(f"- 带 `[Spec-OK]` 前缀的事件：{summary['prefixed_event_count']}")
    status = "通过" if summary.get("status") == "success" else "需关注"
    lines.append(f"- 状态：{status}")

    if summary.get("success_events"):
        lines.append("\n### 成功事件")
        for line in summary["success_events"]:
            lines.append(f"- {line}")

    if summary.get("failure_events"):
        lines.append("\n### 失败/错误事件")
        for line in summary["failure_events"]:
            lines.append(f"- {line}")
    elif summary.get("completed"):
        lines.append("\n未检测到失败事件，流水线已完成。")

    return "\n".join(lines)


def generate_acceptance_report(log_path: Path) -> Tuple[Dict[str, Any], str]:
    content = read_log(log_path)
    if content is None:
        raise FileNotFoundError(str(log_path))
    summary = summarise_log(content, log_path=log_path)
    markdown = render_markdown(summary)
    return summary, markdown


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate acceptance summaries from pipeline logs.")
    parser.add_argument(
        "--log-path",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Path to the pipeline log file (default: logs/pipeline.log)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    log_path: Path = args.log_path
    content = read_log(log_path)
    if content is None:
        print(
            "[Spec-OK] 未找到日志文件。请确认已运行主流程或通过 --log-path 指定有效路径。"
        )
        return 1

    summary = summarise_log(content, log_path=log_path)
    markdown = render_markdown(summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n--- Markdown 摘要 ---\n")
    print(markdown)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
