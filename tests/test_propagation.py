"""
Test suite for the Propagation Node - child node generation with temperature coupling.

These tests are written BEFORE implementation (TDD).
Expected to FAIL until src/agents/propagation.py is implemented.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock


class TestPropagationNodeGeneration:
    """Tests for basic child node generation functionality."""

    def test_generates_correct_number_of_children(self):
        """Each active strategy should spawn m children (m from config)."""
        from src.agents.propagation import propagation_node
        from src.core.state import DeepThinkState
        
        state: DeepThinkState = {
            "problem_state": "Test Problem",
            "strategies": [
                {"id": "p1", "name": "Parent 1", "rationale": "R1", "assumption": "A1",
                 "milestones": [], "embedding": None, "density": None, "log_density": None,
                 "score": 0.5, "status": "active", "trajectory": ["init"]},
                {"id": "p2", "name": "Parent 2", "rationale": "R2", "assumption": "A2",
                 "milestones": [], "embedding": None, "density": None, "log_density": None,
                 "score": 0.6, "status": "active", "trajectory": ["init"]},
            ],
            "research_context": None,
            "spatial_entropy": 0.5,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {
                "children_per_parent": 2,  # m = 2
                "t_max": 2.0,
            },
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.propagation._generate_child_strategy") as mock_gen:
            mock_gen.return_value = {
                "id": "child-new", "name": "Child", "rationale": "CR",
                "assumption": "CA", "milestones": [],
                "embedding": None, "density": None, "log_density": None,
                "score": 0.0, "status": "active", "trajectory": []
            }
            
            new_state = propagation_node(state)
            
            # 2 parents * 2 children = 4 new strategies
            # Original parents should be marked as 'expanded' or kept
            active_count = len([s for s in new_state["strategies"] if s["status"] == "active"])
            # Depending on design: children are active, parents may become 'expanded'
            assert mock_gen.call_count == 4  # 2 parents * 2 children

    def test_children_inherit_parent_trajectory(self):
        """Children should have parent's trajectory + new step."""
        from src.agents.propagation import propagation_node
        
        parent_trajectory = ["step1", "step2"]
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "p1", "name": "Parent", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1, 0.2], "density": 0.5, "log_density": -0.693,
                 "score": 0.5, "status": "active", "trajectory": parent_trajectory.copy()},
            ],
            "research_context": None,
            "spatial_entropy": 0.5,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {"children_per_parent": 1},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.propagation._generate_child_strategy") as mock_gen:
            def create_child(*args, **kwargs):
                # Simulates child inheriting from parent
                return {
                    "id": "child-1", "name": "Child", "rationale": "New R",
                    "assumption": "New A", "milestones": [],
                    "embedding": None, "density": None, "log_density": None,
                    "score": 0.0, "status": "active",
                    "trajectory": parent_trajectory + ["New reasoning step"]
                }
            mock_gen.side_effect = create_child
            
            new_state = propagation_node(state)
            
            # Find child strategy
            children = [s for s in new_state["strategies"] if s["id"] == "child-1"]
            assert len(children) == 1
            assert "step1" in children[0]["trajectory"]
            assert "step2" in children[0]["trajectory"]
            assert "New reasoning step" in children[0]["trajectory"]


class TestTemperatureCoupling:
    """Tests for temperature -> LLM parameter coupling."""

    def test_llm_temperature_derived_from_normalized_temperature(self):
        """LLM temperature should be derived from tau (normalized temperature)."""
        from src.agents.propagation import propagation_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "p1", "name": "Parent", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1], "density": 0.5, "log_density": -0.7,
                 "score": 0.5, "status": "active", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.5,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.7,  # tau = 0.7
            "config": {"children_per_parent": 1},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.propagation.ChatGoogleGenerativeAI") as MockLLM:
            mock_instance = MagicMock()
            MockLLM.return_value = mock_instance
            mock_instance.invoke.return_value = MagicMock(content='{"strategy_name": "C", "rationale": "R", "initial_assumption": "A"}')
            
            propagation_node(state)
            
            # Verify LLM was created with temperature derived from tau
            call_kwargs = MockLLM.call_args.kwargs
            llm_temp = call_kwargs.get("temperature")
            
            # Expected: tau clipped to [0.1, 1.0]
            assert llm_temp is not None
            assert 0.1 <= llm_temp <= 1.0
            assert abs(llm_temp - 0.7) < 0.01  # Should be close to tau=0.7

    def test_temperature_clipped_when_tau_exceeds_one(self):
        """When tau > 1.0, LLM temperature should be clipped to 1.0."""
        from src.agents.propagation import propagation_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "p1", "name": "Parent", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1], "density": 0.5, "log_density": -0.7,
                 "score": 0.5, "status": "active", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.5,
            "effective_temperature": 5.0,
            "normalized_temperature": 2.5,  # tau > 1.0
            "config": {"children_per_parent": 1},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.propagation.ChatGoogleGenerativeAI") as MockLLM:
            mock_instance = MagicMock()
            MockLLM.return_value = mock_instance
            mock_instance.invoke.return_value = MagicMock(content='{"strategy_name": "C", "rationale": "R", "initial_assumption": "A"}')
            
            propagation_node(state)
            
            call_kwargs = MockLLM.call_args.kwargs
            llm_temp = call_kwargs.get("temperature")
            
            assert llm_temp == 1.0  # Should be clipped

    def test_temperature_has_minimum_floor(self):
        """LLM temperature should not go below 0.1 (floor for diversity)."""
        from src.agents.propagation import propagation_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "p1", "name": "Parent", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1], "density": 0.5, "log_density": -0.7,
                 "score": 0.5, "status": "active", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.05,  # Very low entropy
            "effective_temperature": 0.01,
            "normalized_temperature": 0.005,  # tau very close to 0
            "config": {"children_per_parent": 1},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.propagation.ChatGoogleGenerativeAI") as MockLLM:
            mock_instance = MagicMock()
            MockLLM.return_value = mock_instance
            mock_instance.invoke.return_value = MagicMock(content='{"strategy_name": "C", "rationale": "R", "initial_assumption": "A"}')
            
            propagation_node(state)
            
            call_kwargs = MockLLM.call_args.kwargs
            llm_temp = call_kwargs.get("temperature")
            
            assert llm_temp >= 0.1  # Minimum floor


class TestPropagationSkipsInactive:
    """Tests for handling inactive/pruned strategies."""

    def test_does_not_propagate_pruned_strategies(self):
        """Pruned strategies should not generate children."""
        from src.agents.propagation import propagation_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "p1", "name": "Active", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1], "density": 0.5, "log_density": -0.7,
                 "score": 0.8, "status": "active", "trajectory": []},
                {"id": "p2", "name": "Pruned", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1], "density": 0.5, "log_density": -0.7,
                 "score": 0.2, "status": "pruned", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.5,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {"children_per_parent": 2},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.propagation._generate_child_strategy") as mock_gen:
            mock_gen.return_value = {
                "id": "child", "name": "Child", "rationale": "R",
                "assumption": "A", "milestones": [],
                "embedding": None, "density": None, "log_density": None,
                "score": 0.0, "status": "active", "trajectory": []
            }
            
            propagation_node(state)
            
            # Only 1 active parent * 2 children = 2 calls
            assert mock_gen.call_count == 2
