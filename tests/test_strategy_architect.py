"""Tests for the strategy architect generation helper."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import src.strategy_architect as strategy_architect


class DummyResponse:
    def __init__(self, payload: list[dict]):
        self.text = json.dumps(payload, ensure_ascii=False)


class DummyModel:
    def __init__(self):
        self.last_prompt: str | None = None

    def generate_content(self, prompt: str, **_kwargs):  # pragma: no cover - interface compatibility
        self.last_prompt = prompt
        payload = [
            {
                "strategy_name": "探索多模型集成",
                "rationale": "通过多源信息聚合提高鲁棒性",
                "initial_assumption": "存在可组合的信息协调机制",
                "milestones": [
                    "建立冲突信息聚合的评估基线",
                    {"name": "统一表示层", "description": "设计可共享的中间表示"},
                    "在真实任务中验证协作推理质量",
                ],
            }
        ]
        return DummyResponse(payload)


class DummyGenerationConfig:
    def __init__(self, **_kwargs):
        pass


@pytest.fixture
def patched_generation(monkeypatch) -> DummyModel:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(strategy_architect.genai, "configure", lambda **_: None)
    dummy_model = DummyModel()
    monkeypatch.setattr(strategy_architect.genai, "GenerativeModel", lambda **_: dummy_model)
    monkeypatch.setattr(strategy_architect.genai, "types", SimpleNamespace(GenerationConfig=DummyGenerationConfig))
    return dummy_model


def test_generate_strategic_blueprint_returns_milestones(patched_generation: DummyModel):
    results = strategy_architect.generate_strategic_blueprint("problem state", model_name="test")

    assert results, "Expected strategies to be returned"
    strategy = results[0]
    assert "milestones" in strategy
    assert isinstance(strategy["milestones"], list)
    assert strategy["milestones"]
    assert all(m is not None for m in strategy["milestones"])
    assert patched_generation.last_prompt is not None
    assert "milestones" in patched_generation.last_prompt
