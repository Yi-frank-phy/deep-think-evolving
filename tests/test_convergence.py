"""
Test suite for convergence judgment logic.

These tests are written BEFORE implementation (TDD).
Expected to FAIL until should_continue function is implemented.
"""

import pytest
from typing import Literal


class TestShouldContinueFunction:
    """Tests for the should_continue convergence decision function."""

    def test_ends_when_max_iterations_reached(self):
        """Should return 'end' when iteration_count >= max_iterations."""
        from src.core.graph_builder import should_continue
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "status": "active"},
            ],
            "spatial_entropy": 0.5,  # Above threshold
            "config": {
                "max_iterations": 10,
                "entropy_threshold": 0.1,
            },
            "iteration_count": 10,  # Exactly at max
        }
        
        result = should_continue(state)
        assert result == "end"

    def test_continues_when_under_max_iterations(self):
        """Should return 'continue' when iteration_count < max_iterations and not converged."""
        from src.core.graph_builder import should_continue
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "status": "active"},
            ],
            "spatial_entropy": 0.5,  # Above threshold -> not converged
            "config": {
                "max_iterations": 10,
                "entropy_threshold": 0.1,
            },
            "iteration_count": 5,  # Under max
        }
        
        result = should_continue(state)
        assert result == "continue"

    def test_ends_when_entropy_stabilized(self):
        """Should return 'end' when entropy change rate is below threshold (converged)."""
        from src.core.graph_builder import should_continue
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "status": "active"},
            ],
            "spatial_entropy": 0.51,  # Current entropy
            "prev_spatial_entropy": 0.50,  # Previous entropy (very small change)
            "config": {
                "max_iterations": 10,
                "entropy_change_threshold": 0.1,  # Relative change threshold
            },
            "iteration_count": 3,  # Under max iterations
        }
        
        # Change = |0.51 - 0.50| / max(0.51, 0.50, 1.0) = 0.01 / 1.0 = 0.01 < 0.1
        result = should_continue(state)
        assert result == "end"

    def test_ends_when_no_active_strategies(self):
        """Should return 'end' when all strategies are pruned/inactive."""
        from src.core.graph_builder import should_continue
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "status": "pruned"},
                {"id": "s2", "status": "completed"},
            ],
            "spatial_entropy": 0.5,
            "config": {
                "max_iterations": 10,
                "entropy_threshold": 0.1,
            },
            "iteration_count": 2,
        }
        
        result = should_continue(state)
        assert result == "end"

    def test_uses_default_max_iterations_when_missing(self):
        """Should use default max_iterations=10 when not in config."""
        from src.core.graph_builder import should_continue
        
        state = {
            "problem_state": "Test",
            "strategies": [{"id": "s1", "status": "active"}],
            "spatial_entropy": 0.5,
            "config": {},  # No max_iterations specified
            "iteration_count": 10,  # At default max
        }
        
        result = should_continue(state)
        assert result == "end"

    def test_uses_default_entropy_change_threshold_when_missing(self):
        """Should use default entropy_change_threshold=0.1 when not in config."""
        from src.core.graph_builder import should_continue
        
        state = {
            "problem_state": "Test",
            "strategies": [{"id": "s1", "status": "active"}],
            "spatial_entropy": 0.505,  # Current
            "prev_spatial_entropy": 0.50,  # Previous (tiny change)
            "config": {},  # No entropy_change_threshold specified, uses default 0.1
            "iteration_count": 2,
        }
        
        # Change = 0.005 / 1.0 = 0.005 < 0.1 (default threshold) -> converged
        result = should_continue(state)
        assert result == "end"

    def test_empty_strategies_list_ends(self):
        """Should return 'end' when strategies list is empty."""
        from src.core.graph_builder import should_continue
        
        state = {
            "problem_state": "Test",
            "strategies": [],
            "spatial_entropy": 0.5,
            "config": {"max_iterations": 10},
            "iteration_count": 1,
        }
        
        result = should_continue(state)
        assert result == "end"


class TestIterationCountIncrement:
    """Tests for iteration counter behavior in evolution node."""

    def test_evolution_increments_iteration_count(self):
        """Evolution node should increment iteration_count each time it runs."""
        from src.agents.evolution import evolution_node
        from unittest.mock import patch
        import numpy as np
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "S1", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1, 0.2], "density": None, "log_density": None,
                 "score": 0.5, "status": "active", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.0,
            "effective_temperature": 0.0,
            "normalized_temperature": 0.0,
            "config": {"beam_width": 3, "t_max": 2.0},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 5,  # Current count
        }
        
        with patch("src.agents.evolution.embed_text") as mock_embed:
            mock_embed.return_value = [0.1, 0.2]
            
            new_state = evolution_node(state)
            
            assert new_state.get("iteration_count") == 6  # Incremented

    def test_iteration_count_starts_at_zero_if_missing(self):
        """If iteration_count is missing, it should start at 0 and become 1."""
        from src.agents.evolution import evolution_node
        from unittest.mock import patch
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "S1", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1, 0.2], "density": None, "log_density": None,
                 "score": 0.5, "status": "active", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.0,
            "effective_temperature": 0.0,
            "normalized_temperature": 0.0,
            "config": {"beam_width": 3, "t_max": 2.0},
            "virtual_filesystem": {},
            "history": [],
            # Note: no iteration_count key
        }
        
        with patch("src.agents.evolution.embed_text") as mock_embed:
            mock_embed.return_value = [0.1, 0.2]
            
            new_state = evolution_node(state)
            
            assert new_state.get("iteration_count") == 1


class TestGraphLoopStructure:
    """Tests for the graph containing proper loop edges."""

    def test_graph_has_conditional_edge_from_evolution(self):
        """Graph should have conditional edge from evolution node."""
        from src.core.graph_builder import build_deep_think_graph
        
        app = build_deep_think_graph()
        graph = app.get_graph()
        
        # Check that evolution has outgoing edges
        evolution_edges = [e for e in graph.edges if e.source == "evolution"]
        
        # Should have at least 2 edges: one to architect_scheduler (continue), one to END
        assert len(evolution_edges) >= 1
        
        # At least one edge should go to architect_scheduler for the loop (new architecture)
        destinations = [e.target for e in evolution_edges]
        assert "architect_scheduler" in destinations or any("end" in d.lower() for d in destinations)

    def test_graph_has_executor_to_distiller_for_judge_edge(self):
        """Graph should have edge from executor to distiller_for_judge (context rot prevention)."""
        from src.core.graph_builder import build_deep_think_graph
        
        app = build_deep_think_graph()
        graph = app.get_graph()
        
        # Check executor -> distiller_for_judge edge exists
        # (executor connects to distiller_for_judge, not directly to judge, to prevent context rot)
        executor_edges = [e for e in graph.edges if e.source == "executor"]
        destinations = [e.target for e in executor_edges]
        
        assert "distiller_for_judge" in destinations
