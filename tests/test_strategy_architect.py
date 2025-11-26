"""Tests for the strategy architect generation helper."""

from __future__ import annotations

import json
from typing import Any, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from src import strategy_architect


class FakeChatModel(BaseChatModel):
    """A fake chat model for testing."""
    
    responses: List[str]
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=self.responses[0]))]
        )
    
    @property
    def _llm_type(self) -> str:
        return "fake"


def test_generate_strategic_blueprint_returns_nested_milestones(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    expected_payload = [
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
    
    # Create a fake model that returns the expected JSON
    fake_llm = FakeChatModel(responses=[json.dumps(expected_payload)])
    
    # Patch the class to return our fake instance
    monkeypatch.setattr(strategy_architect, "ChatGoogleGenerativeAI", lambda **kwargs: fake_llm)

    blueprint = strategy_architect.generate_strategic_blueprint("example problem", model_name="fake-model")

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
