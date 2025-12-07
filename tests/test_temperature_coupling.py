"""
Test suite for temperature coupling configuration.

Tests the configurable temperature coupling (auto/manual) in propagation.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestTemperatureCouplingModes:
    """Tests for auto/manual temperature coupling."""

    def test_auto_mode_uses_tau(self):
        """Auto mode should derive LLM temp from system tau."""
        from src.agents.propagation import calculate_llm_temperature
        
        # tau = 0.7 should give llm_temp = 0.7 (in [0, 2] range)
        llm_temp = calculate_llm_temperature(tau=0.7, coupling_mode="auto")
        assert llm_temp == 0.7
        
        # tau = 1.5 should give llm_temp = 1.5
        llm_temp = calculate_llm_temperature(tau=1.5, coupling_mode="auto")
        assert llm_temp == 1.5

    def test_auto_mode_clips_to_range(self):
        """Auto mode should clip to [0, 2] for Gemini API."""
        from src.agents.propagation import calculate_llm_temperature
        
        # tau = 3.0 should clip to 2.0 (max)
        llm_temp = calculate_llm_temperature(tau=3.0, coupling_mode="auto")
        assert llm_temp == 2.0
        
        # tau = -0.5 should clip to 0.0 (min)
        llm_temp = calculate_llm_temperature(tau=-0.5, coupling_mode="auto")
        assert llm_temp == 0.0

    def test_manual_mode_uses_fixed_temp(self):
        """Manual mode should use fixed temperature, ignoring tau."""
        from src.agents.propagation import calculate_llm_temperature
        
        # Default manual temp is 1.0
        llm_temp = calculate_llm_temperature(tau=0.2, coupling_mode="manual")
        assert llm_temp == 1.0
        
        # Even with high tau, should still be 1.0
        llm_temp = calculate_llm_temperature(tau=2.5, coupling_mode="manual")
        assert llm_temp == 1.0

    def test_manual_mode_custom_temp(self):
        """Manual mode should use custom temp when specified."""
        from src.agents.propagation import calculate_llm_temperature
        
        llm_temp = calculate_llm_temperature(
            tau=0.5, coupling_mode="manual", manual_temp=0.3
        )
        assert llm_temp == 0.3

    def test_default_coupling_is_auto(self):
        """Default coupling mode should be 'auto'."""
        from src.agents.propagation import calculate_llm_temperature
        
        # When coupling_mode not specified, should behave like auto
        llm_temp = calculate_llm_temperature(tau=0.8)
        assert llm_temp == 0.8


class TestPropagationWithCoupling:
    """Tests for propagation node using different coupling modes."""

    def test_propagation_respects_coupling_config(self):
        """Propagation should read coupling mode from config."""
        from src.agents.propagation import propagation_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "p1", "name": "Parent", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1], "density": 0.5, "log_density": -0.7,
                 "score": 0.5, "status": "active", "trajectory": [], "child_quota": 1},
            ],
            "research_context": None,
            "spatial_entropy": 0.5,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.3,  # tau = 0.3
            "config": {
                "temperature_coupling": "manual",  # Decouple
                "manual_llm_temperature": 0.8,
            },
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.propagation.ChatGoogleGenerativeAI") as MockLLM:
            mock_instance = MagicMock()
            MockLLM.return_value = mock_instance
            mock_instance.invoke.return_value = MagicMock(
                content='{"strategy_name": "C", "rationale": "R", "initial_assumption": "A", "new_step": "S"}'
            )
            
            with patch("src.agents.propagation.os.environ.get") as mock_env:
                mock_env.side_effect = lambda k, d=None: {"GEMINI_API_KEY": "test"}.get(k, d)
                
                propagation_node(state)
            
            # Verify LLM was called with manual temp (0.8), not tau (0.3)
            call_kwargs = MockLLM.call_args.kwargs
            assert call_kwargs["temperature"] == 0.8

    def test_propagation_uses_child_quota(self):
        """Propagation should use child_quota from Boltzmann allocation."""
        from src.agents.propagation import propagation_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "p1", "name": "High Value", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1], "density": 0.5, "log_density": -0.7,
                 "score": 0.9, "status": "active", "trajectory": [], "child_quota": 3},
                {"id": "p2", "name": "Low Value", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.2], "density": 0.5, "log_density": -0.7,
                 "score": 0.1, "status": "active", "trajectory": [], "child_quota": 1},
            ],
            "research_context": None,
            "spatial_entropy": 0.5,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.propagation.os.environ.get") as mock_env:
            mock_env.side_effect = lambda k, d=None: {"USE_MOCK_AGENTS": "true"}.get(k, d)
            
            new_state = propagation_node(state)
        
        # Should create 3 + 1 = 4 children total
        new_children = [s for s in new_state["strategies"] if "Variant" in s["name"]]
        assert len(new_children) == 4
        
        # 3 children from high value parent
        high_value_children = [c for c in new_children if c["parent_id"] == "p1"]
        assert len(high_value_children) == 3

    def test_propagation_skips_zero_quota(self):
        """Strategies with child_quota=0 should not generate children."""
        from src.agents.propagation import propagation_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "p1", "name": "Has Quota", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1], "density": 0.5, "log_density": -0.7,
                 "score": 0.9, "status": "active", "trajectory": [], "child_quota": 2},
                {"id": "p2", "name": "No Quota", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.2], "density": 0.5, "log_density": -0.7,
                 "score": 0.1, "status": "active", "trajectory": [], "child_quota": 0},
            ],
            "research_context": None,
            "spatial_entropy": 0.5,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.propagation.os.environ.get") as mock_env:
            mock_env.side_effect = lambda k, d=None: {"USE_MOCK_AGENTS": "true"}.get(k, d)
            
            new_state = propagation_node(state)
        
        # Only 2 children (from p1), p2 has 0 quota
        new_children = [s for s in new_state["strategies"] if "Variant" in s["name"]]
        assert len(new_children) == 2
        
        # All children should be from p1
        for c in new_children:
            assert c["parent_id"] == "p1"
