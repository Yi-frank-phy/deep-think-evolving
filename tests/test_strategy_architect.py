import json
import types

import google.generativeai as genai

from src.strategy_architect import generate_strategic_blueprint


class _DummyResponse:
    def __init__(self, payload: list[dict]):
        self.text = json.dumps(payload, ensure_ascii=False)


class _DummyModel:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def generate_content(self, *_args, **_kwargs):
        return _DummyResponse(
            [
                {
                    "strategy_name": "Alpha",
                    "rationale": "多通路探索",
                    "initial_assumption": "问题具有多阶段结构",
                    "milestones": {
                        "阶段 1: 诊断": [
                            {
                                "title": "访谈关键用户",
                                "summary": "与目标用户确认首要痛点",
                                "success_criteria": ["完成 5 次访谈", "形成洞察清单"],
                            }
                        ],
                        "阶段 2: 验证": [
                            {
                                "title": "设计小规模实验",
                                "summary": "在受控环境中验证假设",
                                "success_criteria": ["实验完成", "收集关键指标"],
                            }
                        ],
                    },
                }
            ]
        )


def test_generate_strategic_blueprint_returns_nested_milestones(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    monkeypatch.setattr(genai, "configure", lambda api_key: None)
    monkeypatch.setattr(genai, "GenerativeModel", lambda **kwargs: _DummyModel(**kwargs))

    monkeypatch.setattr(
        genai,
        "types",
        types.SimpleNamespace(GenerationConfig=lambda **kwargs: types.SimpleNamespace(**kwargs)),
    )

    blueprint = generate_strategic_blueprint("example problem", model_name="fake-model")

    assert blueprint
    strategy = blueprint[0]
    assert "milestones" in strategy
    assert isinstance(strategy["milestones"], dict)
    assert set(strategy["milestones"].keys()) == {"阶段 1: 诊断", "阶段 2: 验证"}

    for phase, milestones in strategy["milestones"].items():
        assert isinstance(phase, str)
        assert isinstance(milestones, list)
        assert milestones
        assert all("title" in item and "summary" in item for item in milestones)
        assert all(isinstance(item.get("success_criteria"), list) for item in milestones)
