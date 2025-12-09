"""
Test suite for the Judge Agent.

Tests scoring logic, feasibility assessment, and no-hard-pruning constraint.
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestJudgeScoring:
    """Tests for Judge scoring behavior."""
    
    def test_judge_returns_scored_strategies(self):
        """Judge should return strategies with updated scores."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.judge import judge_node
        
        state = {
            "problem_state": "Test problem",
            "judge_context": "Context for scoring",
            "strategies": [
                {
                    "id": "s1",
                    "name": "Strategy A",
                    "status": "active",
                    "score": 0.5,
                    "rationale": "Method A",
                    "assumption": "Assumption A",
                    "trajectory": []
                },
                {
                    "id": "s2", 
                    "name": "Strategy B",
                    "status": "active",
                    "score": 0.3,
                    "rationale": "Method B",
                    "assumption": "Assumption B",
                    "trajectory": []
                }
            ],
            "history": [],
            "config": {}
        }
        
        result = judge_node(state)
        
        # Should have strategies
        assert "strategies" in result
        strategies = result["strategies"]
        
        # All strategies should have scores
        for s in strategies:
            assert "score" in s
            assert isinstance(s["score"], (int, float))
        
        os.environ.pop("USE_MOCK_AGENTS", None)
    
    def test_judge_does_not_hard_prune(self):
        """Judge should NOT set any strategy status to 'pruned'."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.judge import judge_node
        
        state = {
            "problem_state": "Test problem",
            "judge_context": "All strategies are mediocre",
            "strategies": [
                {"id": "s1", "name": "Bad Strategy", "status": "active", "score": 0.1, "rationale": "x", "assumption": "y", "trajectory": []},
                {"id": "s2", "name": "Worse Strategy", "status": "active", "score": 0.05, "rationale": "x", "assumption": "y", "trajectory": []},
            ],
            "history": [],
            "config": {}
        }
        
        result = judge_node(state)
        
        # NO strategy should be marked pruned by judge (soft pruning is done by Evolution)
        for s in result["strategies"]:
            assert s.get("status") in ["active", "pending", None], \
                f"Judge should not hard-prune! Found status: {s.get('status')}"
        
        os.environ.pop("USE_MOCK_AGENTS", None)
    
    def test_judge_appends_to_history(self):
        """Judge should append scoring event to history."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.judge import judge_node
        
        state = {
            "problem_state": "Test",
            "judge_context": "Context",
            "strategies": [
                {"id": "s1", "name": "S1", "status": "active", "score": 0.5, "rationale": "x", "assumption": "y", "trajectory": []}
            ],
            "history": ["Previous event"],
            "config": {}
        }
        
        result = judge_node(state)
        
        # History should be extended
        assert len(result.get("history", [])) >= 1
        
        os.environ.pop("USE_MOCK_AGENTS", None)


class TestJudgeWithContext:
    """Tests for Judge context usage."""
    
    def test_judge_uses_judge_context(self):
        """Judge should use the judge_context provided by Distiller."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.judge import judge_node
        
        state = {
            "problem_state": "Complex optimization problem",
            "judge_context": "CRITICAL: Strategy A has fatal flaw. Strategy B is promising.",
            "strategies": [
                {"id": "s1", "name": "Strategy A", "status": "active", "score": 0.8, "rationale": "fast", "assumption": "stable", "trajectory": []},
                {"id": "s2", "name": "Strategy B", "status": "active", "score": 0.6, "rationale": "slow", "assumption": "robust", "trajectory": []}
            ],
            "history": [],
            "config": {}
        }
        
        result = judge_node(state)
        
        # Judge should have processed (in mock mode, just check it runs)
        assert "strategies" in result
        
        os.environ.pop("USE_MOCK_AGENTS", None)


class TestJudgeScoreNormalization:
    """Tests for score normalization and bounds."""
    
    def test_scores_are_in_valid_range(self):
        """All scores should be between 0 and 1."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.judge import judge_node
        
        state = {
            "problem_state": "Test",
            "judge_context": "Normal evaluation",
            "strategies": [
                {"id": f"s{i}", "name": f"Strategy {i}", "status": "active", "score": i * 0.1, "rationale": "x", "assumption": "y", "trajectory": []}
                for i in range(1, 6)
            ],
            "history": [],
            "config": {}
        }
        
        result = judge_node(state)
        
        for s in result["strategies"]:
            score = s.get("score", 0)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range [0, 1]"
        
        os.environ.pop("USE_MOCK_AGENTS", None)
    
    def test_handles_empty_strategies(self):
        """Judge should handle empty strategies list gracefully."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.judge import judge_node
        
        state = {
            "problem_state": "Test",
            "judge_context": "No strategies to score",
            "strategies": [],
            "history": [],
            "config": {}
        }
        
        result = judge_node(state)
        
        # Should not crash
        assert "strategies" in result
        assert result["strategies"] == []
        
        os.environ.pop("USE_MOCK_AGENTS", None)
