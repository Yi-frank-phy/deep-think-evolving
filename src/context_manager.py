"""Utilities for managing per-thread reasoning contexts and long-term reflections."""
from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import google.generativeai as genai

from src.embedding_client import embed_text


BASE_DIR = Path(__file__).resolve().parents[1]
CONTEXT_ROOT = BASE_DIR / "runtime_contexts"
KNOWLEDGE_BASE_ROOT = BASE_DIR / "knowledge_base"
DEFAULT_MODEL_NAME = os.getenv("SUMMARY_MODEL_NAME", "gemini-1.5-flash")
DEFAULT_INITIAL_PROMPT = """# Strategy Thread Bootstrapping\n\n- Thread ID: {thread_id}\n- Created (UTC): {timestamp}\n\nMaintain a detailed stream-of-consciousness reasoning log for this strategy branch.\nEach step should be appended as a JSON line in ``history.log`` using the ``append_step``\nhelper so downstream tooling can parse the progression of thought.\n"""
DEFAULT_HISTORY_LIMIT = 50
HISTORY_LIMIT_ENV_VAR = "CONTEXT_HISTORY_LIMIT"
SUMMARY_FILENAME = "summary.md"


@dataclass(slots=True)
class SummaryResult:
    """Encapsulates the stored summary for a reasoning thread."""

    path: Path
    text: str


@dataclass(slots=True)
class HistoryEntry:
    """Represents a single reasoning step stored in history.log."""

    timestamp: str
    data: Any

    @property
    def rendered(self) -> str:
        body: str
        if isinstance(self.data, (dict, list)):
            body = json.dumps(self.data, ensure_ascii=False, indent=2)
        else:
            body = str(self.data)
        return f"[{self.timestamp}]\n{body}"


def _ensure_directories() -> None:
    CONTEXT_ROOT.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_BASE_ROOT.mkdir(parents=True, exist_ok=True)
    # Preserve git tracking placeholder if repository is clean
    gitkeep = KNOWLEDGE_BASE_ROOT / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()


def _sanitize_thread_id(thread_id: str) -> str:
    cleaned = thread_id.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned or "thread"


def _context_dir(thread_id: str) -> Path:
    _ensure_directories()
    return CONTEXT_ROOT / _sanitize_thread_id(thread_id)


def create_context(thread_id: str) -> Path:
    """Create an isolated directory for a strategy thread and seed the prompt."""
    context_dir = _context_dir(thread_id)
    context_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    prompt_text = DEFAULT_INITIAL_PROMPT.format(thread_id=thread_id, timestamp=timestamp)
    prompt_path = context_dir / "prompt.md"
    prompt_path.write_text(prompt_text, encoding="utf-8")

    history_path = context_dir / "history.log"
    if not history_path.exists():
        history_path.write_text("", encoding="utf-8")

    return context_dir


def append_step(thread_id: str, step_data: Any) -> Path:
    """Append a reasoning step to the thread's history log."""
    context_dir = _context_dir(thread_id)
    if not context_dir.exists():
        raise FileNotFoundError(
            f"Context for '{thread_id}' does not exist. Did you call create_context()?"
        )

    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "thread_id": _sanitize_thread_id(thread_id),
        "data": step_data,
    }

    history_path = context_dir / "history.log"
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False))
        handle.write("\n")

    _enforce_history_limit(history_path)

    return history_path


def get_history_limit() -> int:
    """Return the configured maximum number of history entries to retain."""

    raw_value = os.getenv(HISTORY_LIMIT_ENV_VAR)
    if raw_value is None or not raw_value.strip():
        return DEFAULT_HISTORY_LIMIT

    try:
        parsed = int(raw_value)
        if parsed < 1:
            raise ValueError
        return parsed
    except (TypeError, ValueError):
        return DEFAULT_HISTORY_LIMIT


def _load_history(thread_id: str) -> list[HistoryEntry]:
    context_dir = _context_dir(thread_id)
    history_path = context_dir / "history.log"
    if not history_path.exists():
        return []

    entries: list[HistoryEntry] = []
    with history_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                entries.append(
                    HistoryEntry(
                        timestamp=payload.get("timestamp", ""),
                        data=payload.get("data"),
                    )
                )
            except json.JSONDecodeError:
                entries.append(
                    HistoryEntry(timestamp="", data=line.strip())
                )
    limit = get_history_limit()
    return entries[-limit:]


def _format_history(entries: Iterable[HistoryEntry]) -> str:
    formatted = [entry.rendered for entry in entries]
    return "\n\n".join(formatted) if formatted else "(no reasoning steps recorded yet)"


def _enforce_history_limit(history_path: Path) -> None:
    """Trim the history log so that at most the configured history limit remain."""

    if not history_path.exists():
        return

    with history_path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    limit = get_history_limit()

    if len(lines) <= limit:
        return

    trimmed = lines[-limit:]
    with history_path.open("w", encoding="utf-8") as handle:
        handle.writelines(trimmed)


def _generate_summary(thread_id: str, prompt_text: str, history_block: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback_summary(thread_id, history_block)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=DEFAULT_MODEL_NAME)

    system_instruction = (
        "你是一位系统日志分析师。你的任务是将思维链（stream-of-consciousness）" "记录总结成结构化洞察。"
    )
    user_prompt = f"""
请阅读以下上下文，生成一份全面的 SoC（Stream of Consciousness）摘要，包含：
1. 此策略线程目前关注的核心目标或任务。
2. 已采取的关键行动步骤（保持顺序）。
3. 仍存在的开放性问题或下一步计划。
4. 若日志中出现了异常或待跟进事项，请在最后列出待办事项列表。

=== 初始 Prompt ===
{prompt_text}

=== 历史推理日志（按时间倒序，最近的在最后） ===
{history_block}

输出使用 Markdown，包含清晰的小节标题。
"""

    try:
        response = model.generate_content(
            [
                {"role": "system", "parts": [system_instruction]},
                {"role": "user", "parts": [user_prompt]},
            ]
        )
        if not response or not getattr(response, "text", "").strip():
            raise RuntimeError("Empty response from model")
        return response.text.strip()
    except Exception:
        return _fallback_summary(thread_id, history_block)


def _fallback_summary(thread_id: str, history_block: str) -> str:
    timestamp = datetime.now(timezone.utc).isoformat()
    snippet = history_block.splitlines()
    snippet_text = "\n".join(snippet[-10:]) if snippet else "无历史记录可用于总结。"
    return (
        f"# Thread {thread_id} Summary (Fallback)\n\n"
        "无法访问 Gemini 模型，改为提供最近日志的压缩片段。\n\n"
        "## 最近记录片段\n"
        f"```\n{snippet_text}\n```\n"
        f"\n_生成时间 (UTC): {timestamp}_\n"
    )


def summarize(thread_id: str) -> Path:
    """Generate a SoC summary for the thread and persist it as working memory."""
    context_dir = _context_dir(thread_id)
    if not context_dir.exists():
        raise FileNotFoundError(
            f"Context for '{thread_id}' does not exist. Did you call create_context()?"
        )

    prompt_path = context_dir / "prompt.md"
    prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

    history_entries = _load_history(thread_id)
    history_block = _format_history(history_entries)

    summary_text = _generate_summary(thread_id, prompt_text, history_block)

    summary_path = context_dir / SUMMARY_FILENAME
    summary_path.write_text(summary_text, encoding="utf-8")

    return summary_path


def generate_summary(thread_id: str) -> SummaryResult:
    """Wrapper returning the stored summary metadata and text."""

    summary_path = summarize(thread_id)
    return SummaryResult(path=summary_path, text=summary_path.read_text(encoding="utf-8"))


def _summary_path(thread_id: str) -> Path:
    return _context_dir(thread_id) / SUMMARY_FILENAME


def record_reflection(
    thread_id: str,
    reflection_text: str,
    *,
    outcome: str,
    metadata: Optional[Mapping[str, Any]] = None,
) -> Path:
    """Persist a long-term reflection with embedding metadata into the knowledge base."""

    context_dir = _context_dir(thread_id)
    if not context_dir.exists():
        raise FileNotFoundError(
            f"Context for '{thread_id}' does not exist. Did you call create_context()?"
        )

    timestamp = datetime.now(timezone.utc).isoformat()
    sanitized_id = _sanitize_thread_id(thread_id)
    entry_id = f"{timestamp.replace('-', '').replace(':', '').replace('.', '')}-{uuid.uuid4().hex[:8]}"

    summary_path = _summary_path(thread_id)
    entry_payload = {
        "id": entry_id,
        "thread_id": sanitized_id,
        "thread_label": thread_id,
        "created_at": timestamp,
        "outcome": outcome,
        "reflection": reflection_text,
        "embedding": embed_text(reflection_text),
        "source": {
            "summary_path": str(summary_path) if summary_path.exists() else None,
            "metadata": dict(metadata or {}),
        },
    }

    entry_path = KNOWLEDGE_BASE_ROOT / f"{entry_id}.json"
    entry_path.write_text(json.dumps(entry_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry_path


__all__ = [
    "create_context",
    "append_step",
    "summarize",
    "generate_summary",
    "record_reflection",
    "SummaryResult",
]
