from __future__ import annotations

from logging_helper import SpecLogger, ensure_spec_logger, log_with_spec_prefix


def test_spec_logger_adds_prefix():
    messages: list[str] = []
    logger = SpecLogger(base_logger=messages.append)

    logger("关键事件")

    assert messages == ["[Spec-OK] 关键事件"]


def test_spec_logger_formats_multiline():
    messages: list[str] = []
    logger = SpecLogger(base_logger=messages.append)

    logger("第一行\n第二行")

    assert messages[0] == "[Spec-OK] 第一行\n[Spec-OK] 第二行"


def test_ensure_spec_logger_reuses_instance():
    sink: list[str] = []
    base_logger = SpecLogger(base_logger=sink.append)

    resolved = ensure_spec_logger(base_logger)
    resolved("事件")

    assert resolved is base_logger
    assert sink[-1].startswith("[Spec-OK]")


def test_log_with_spec_prefix_supports_plain_callable():
    captured: list[str] = []

    log_with_spec_prefix("test", logger=captured.append)

    assert captured == ["[Spec-OK] test"]
