"""Utility helpers for standardized specification logging."""

from __future__ import annotations

from typing import Callable, Iterable


SpecEmitter = Callable[[str], None]


def emit_spec_event(emit: SpecEmitter, tag: str, message: str) -> None:
    """Emit a log line annotated with a ``[Spec-<tag>]`` prefix.

    The helper normalises multi-line payloads so each output line carries the
    requested tag. This makes it easier for downstream tooling to extract
    structured status updates from otherwise free-form logs.
    """

    normalized_tag = tag.strip().upper() or "INFO"
    prefix = f"[Spec-{normalized_tag}] "
    lines: Iterable[str]
    if message:
        lines = str(message).splitlines()
    else:
        # Preserve intentional blank lines while keeping the prefix visible.
        lines = [""]

    for line in lines:
        content = line.rstrip()
        emit(f"{prefix}{content}" if content else prefix.rstrip())


__all__ = ["emit_spec_event", "SpecEmitter"]

