"""Utility helpers for emitting Spec Kit compliant log messages."""

from __future__ import annotations

from typing import Callable, Optional, Protocol

Logger = Callable[[str], None]

_DEFAULT_PREFIX = "[Spec-OK] "


class _SupportsCall(Protocol):
    def __call__(self, message: str) -> None:  # pragma: no cover - protocol definition
        ...


class SpecLogger:
    """Logger that ensures messages are prefixed with ``[Spec-OK]``."""

    def __init__(
        self,
        base_logger: Optional[Logger] = None,
        *,
        prefix: str = _DEFAULT_PREFIX,
    ) -> None:
        self.base_logger: Logger = base_logger or print
        self.prefix = prefix

    def format(self, message: str) -> str:
        text = str(message)
        trailing_newline = text.endswith("\n")
        if trailing_newline:
            text = text[:-1]
        if not text:
            formatted = self.prefix.rstrip()
        else:
            lines = text.splitlines()
            formatted_lines = [self._prefix_line(line) for line in lines]
            formatted = "\n".join(formatted_lines)
        if trailing_newline:
            formatted += "\n"
        return formatted

    def _prefix_line(self, line: str) -> str:
        if line.startswith(self.prefix):
            return line
        return f"{self.prefix}{line}"

    def emit(self, message: str) -> str:
        formatted = self.format(message)
        self.base_logger(formatted)
        return formatted

    def log(self, message: str) -> str:
        return self.emit(message)

    def __call__(self, message: str) -> None:
        self.emit(message)


def create_spec_logger(
    logger: Optional[Logger] = None,
    *,
    prefix: str = _DEFAULT_PREFIX,
) -> SpecLogger:
    return SpecLogger(base_logger=logger, prefix=prefix)


def ensure_spec_logger(
    logger: Optional[_SupportsCall | Logger] = None,
    *,
    prefix: str = _DEFAULT_PREFIX,
) -> SpecLogger:
    if isinstance(logger, SpecLogger):
        if logger.prefix == prefix:
            return logger
        return SpecLogger(base_logger=logger.base_logger, prefix=prefix)

    if logger is None:
        return SpecLogger(prefix=prefix)

    return SpecLogger(base_logger=logger, prefix=prefix)


def log_with_spec_prefix(
    message: str,
    logger: Optional[_SupportsCall | Logger] = None,
    *,
    prefix: str = _DEFAULT_PREFIX,
) -> str:
    spec_logger = ensure_spec_logger(logger, prefix=prefix)
    return spec_logger.emit(message)


__all__ = [
    "Logger",
    "SpecLogger",
    "create_spec_logger",
    "ensure_spec_logger",
    "log_with_spec_prefix",
]
