"""
Test suite for the Distiller Agent.

Tests dynamic distillation trigger, context compression, and judge context generation.
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestDistillerTokenEstimation:
    """Tests for token count estimation."""
    
    def test_estimate_token_count_with_strategies(self):
        """Should estimate tokens based on strategies and history."""
        from src.agents.distiller import estimate_token_count
        
        state = {
            "problem_state": "A" * 100,  # 100 chars
            "strategies": [
                {"name": "S1", "rationale": "B" * 200, "assumption": "C" * 100, "trajectory": ["step1", "step2"]},
                {"name": "S2", "rationale": "D" * 200, "assumption": "E" * 100, "trajectory": []},
            ],
            "history": ["event1" * 50, "event2" * 50],
            "research_context": "F" * 500,
            "config": {}
        }
        
        token_count = estimate_token_count(state)
        
        # Should be a positive integer
        assert token_count > 0
        # Should be roughly total_chars / 4 (rough estimate)
        expected_min = 200  # At least some tokens
        assert token_count >= expected_min
    
    def test_estimate_token_count_with_empty_state(self):
        """Should handle empty state gracefully."""
        from src.agents.distiller import estimate_token_count
        
        state = {
            "problem_state": "",
            "strategies": [],
            "history": [],
            "config": {}
        }
        
        token_count = estimate_token_count(state)
        
        # Should return 0 or small number for empty state
        assert token_count >= 0


class TestDistillerShouldDistillLogic:
    """Tests for the should_distill decision function."""
    
    def test_should_distill_returns_true_when_over_threshold(self):
        """Should return True when estimated tokens exceed threshold."""
        from src.agents.distiller import should_distill
        
        state = {
            "problem_state": "X" * 10000,  # Many chars
            "strategies": [
                {"name": f"S{i}", "rationale": "Y" * 500, "assumption": "Z" * 200, "trajectory": ["x" * 100] * 10}
                for i in range(5)
            ],
            "history": ["event" * 100] * 20,
            "research_context": "W" * 5000,
            "config": {"distill_threshold": 1000}  # Low threshold
        }
        
        result = should_distill(state)
        assert result is True
    
    def test_should_distill_returns_false_when_under_threshold(self):
        """Should return False when estimated tokens below threshold."""
        from src.agents.distiller import should_distill
        
        state = {
            "problem_state": "Short",
            "strategies": [{"name": "S1", "rationale": "Brief", "assumption": "A", "trajectory": []}],
            "history": [],
            "config": {"distill_threshold": 100000}  # High threshold
        }
        
        result = should_distill(state)
        assert result is False
    
    def test_uses_default_threshold_when_missing(self):
        """Should use default threshold when not in config."""
        from src.agents.distiller import should_distill
        
        state = {
            "problem_state": "Test",
            "strategies": [],
            "history": [],
            "config": {}  # No distill_threshold
        }
        
        # Should not raise, should use default
        result = should_distill(state)
        assert result in [True, False]


class TestDistillerForJudgeNode:
    """Tests for the distiller_for_judge_node function."""
    
    def test_distiller_for_judge_generates_context(self):
        """Should generate judge_context field."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.distiller import distiller_for_judge_node
        
        state = {
            "problem_state": "Test problem for distillation",
            "strategies": [
                {
                    "id": "s1",
                    "name": "Strategy One",
                    "rationale": "Reasoning here",
                    "assumption": "Key assumption",
                    "status": "active",
                    "score": 0.75,
                    "trajectory": ["step1", "step2"]
                }
            ],
            "history": ["Event 1", "Event 2"],
            "spatial_entropy": 0.5,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {}
        }
        
        result = distiller_for_judge_node(state)
        
        # Should have judge_context field
        assert "judge_context" in result
        assert isinstance(result["judge_context"], str)
        assert len(result["judge_context"]) > 0
        
        os.environ.pop("USE_MOCK_AGENTS", None)
    
    def test_judge_context_includes_strategy_summary(self):
        """Judge context should summarize strategies."""
        from src.agents.distiller import generate_judge_context
        
        state = {
            "problem_state": "Solve complex problem",
            "strategies": [
                {"id": "s1", "name": "Direct Approach", "status": "active", "score": 0.8, "trajectory": ["progress"]},
                {"id": "s2", "name": "Indirect Approach", "status": "active", "score": 0.6, "trajectory": []},
            ],
            "history": ["Iteration 1 complete"],
            "spatial_entropy": 0.3,
            "effective_temperature": 0.8,
            "normalized_temperature": 0.4,
            "config": {}
        }
        
        context = generate_judge_context(state)
        
        # Should mention strategy names
        assert "Direct Approach" in context
        assert "Indirect Approach" in context


class TestDistillerNodeMockMode:
    """Tests for distiller_node in mock mode."""
    
    def test_distiller_node_appends_to_history(self):
        """Distiller should append to history when run."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.distiller import distiller_node
        
        state = {
            "problem_state": "Test",
            "research_context": "Some research context to distill",
            "strategies": [],
            "history": ["Previous event"],
            "config": {}
        }
        
        result = distiller_node(state)
        
        # History should have new entry
        assert len(result.get("history", [])) >= 1
        
        os.environ.pop("USE_MOCK_AGENTS", None)
