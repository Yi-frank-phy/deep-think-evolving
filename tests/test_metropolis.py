"""
Test suite for Metropolis probabilistic pruning.

These tests are written BEFORE implementation (TDD).
Expected to FAIL until metropolis pruning is implemented in evolution.py.
"""

import pytest
import numpy as np
import math
from unittest.mock import patch, MagicMock


class TestMetropolisPruningLogic:
    """Tests for the core Metropolis acceptance criterion."""

    def test_high_temperature_saves_low_score_strategies(self):
        """At high temperature, even low-score strategies have good chance of survival."""
        from src.agents.evolution import metropolis_rescue
        
        # High temperature = more likely to accept bad solutions
        t_eff = 10.0
        best_score = 0.9
        
        pruned_strategies = [
            {"id": "s1", "name": "Low Score", "score": 0.3, "status": "pruned_beam"},
        ]
        
        # With high T, prob = exp(-(0.9-0.3)/10) = exp(-0.06) ≈ 0.94
        # So most of the time it should be rescued
        
        # Run multiple times and count rescues
        rescue_count = 0
        trials = 100
        
        for _ in range(trials):
            result = metropolis_rescue(pruned_strategies.copy(), best_score, t_eff)
            if result[0]["status"] == "active":
                rescue_count += 1
        
        # At high T, expect high rescue rate (>50%)
        assert rescue_count > 50, f"Expected >50 rescues at high T, got {rescue_count}"

    def test_low_temperature_rarely_saves_low_score(self):
        """At low temperature, low-score strategies rarely survive."""
        from src.agents.evolution import metropolis_rescue
        
        # Low temperature = less likely to accept bad solutions
        t_eff = 0.01
        best_score = 0.9
        
        pruned_strategies = [
            {"id": "s1", "name": "Low Score", "score": 0.3, "status": "pruned_beam"},
        ]
        
        # With low T, prob = exp(-(0.9-0.3)/0.01) = exp(-60) ≈ 0
        # Almost never rescued
        
        rescue_count = 0
        trials = 100
        
        for _ in range(trials):
            result = metropolis_rescue(pruned_strategies.copy(), best_score, t_eff)
            if result[0]["status"] == "active":
                rescue_count += 1
        
        # At low T, expect very few rescues (<10%)
        assert rescue_count < 10, f"Expected <10 rescues at low T, got {rescue_count}"

    def test_equal_score_always_rescued(self):
        """When score equals best_score, delta=0, prob=1, always rescued."""
        from src.agents.evolution import metropolis_rescue
        
        t_eff = 1.0
        best_score = 0.5
        
        pruned_strategies = [
            {"id": "s1", "name": "Equal Score", "score": 0.5, "status": "pruned_beam"},
        ]
        
        # delta = 0, prob = exp(0) = 1.0
        for _ in range(10):
            result = metropolis_rescue(pruned_strategies.copy(), best_score, t_eff)
            assert result[0]["status"] == "active"

    def test_trajectory_marked_on_rescue(self):
        """Rescued strategies should have trajectory marked."""
        from src.agents.evolution import metropolis_rescue
        
        t_eff = 100.0  # Very high T to guarantee rescue
        best_score = 0.9
        
        pruned_strategies = [
            {"id": "s1", "name": "Test", "score": 0.5, "status": "pruned_beam", "trajectory": ["init"]},
        ]
        
        result = metropolis_rescue(pruned_strategies.copy(), best_score, t_eff)
        
        if result[0]["status"] == "active":
            assert "Metropolis" in " ".join(result[0]["trajectory"])


class TestMetropolisInEvolutionLoop:
    """Tests for Metropolis integration in the evolution node."""

    def test_evolution_applies_metropolis_after_beam_pruning(self):
        """Evolution node should apply Metropolis rescue after hard beam pruning."""
        from src.agents.evolution import evolution_node
        
        # Create state with more strategies than beam width
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "Best", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1, 0.2], "density": 0.5, "log_density": -0.7,
                 "score": 0.9, "status": "active", "trajectory": []},
                {"id": "s2", "name": "Good", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.2, 0.3], "density": 0.5, "log_density": -0.7,
                 "score": 0.7, "status": "active", "trajectory": []},
                {"id": "s3", "name": "Medium", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.3, 0.4], "density": 0.5, "log_density": -0.7,
                 "score": 0.5, "status": "active", "trajectory": []},
                {"id": "s4", "name": "Low", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.4, 0.5], "density": 0.5, "log_density": -0.7,
                 "score": 0.3, "status": "active", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.0,
            "effective_temperature": 0.0,
            "normalized_temperature": 0.0,
            "config": {
                "beam_width": 2,  # Only keep top 2
                "t_max": 2.0,
            },
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        # Patch metropolis_rescue to count calls
        with patch("src.agents.evolution.metropolis_rescue") as mock_metro:
            mock_metro.return_value = []  # No rescues for simplicity
            
            with patch("src.agents.evolution.embed_text") as mock_embed:
                mock_embed.return_value = [0.1, 0.2]
                
                evolution_node(state)
                
                # Verify metropolis_rescue was called
                mock_metro.assert_called_once()
                
                # Check it was called with pruned strategies
                call_args = mock_metro.call_args
                pruned_list = call_args[0][0]
                assert len(pruned_list) == 2  # 4 strategies - 2 beam = 2 pruned


class TestMetropolisProbabilityCalculation:
    """Tests for the probability calculation itself."""

    def test_probability_formula_correct(self):
        """Verify P = exp(-delta/T) is calculated correctly."""
        from src.agents.evolution import calculate_metropolis_probability
        
        # Test case: delta=0.6, T=1.0
        prob = calculate_metropolis_probability(delta=0.6, t_eff=1.0)
        expected = math.exp(-0.6 / 1.0)
        assert abs(prob - expected) < 1e-6

    def test_probability_clipped_at_one(self):
        """Probability should never exceed 1.0."""
        from src.agents.evolution import calculate_metropolis_probability
        
        # Negative delta (shouldn't happen but test anyway)
        prob = calculate_metropolis_probability(delta=-0.5, t_eff=1.0)
        assert prob <= 1.0

    def test_handles_zero_temperature_safely(self):
        """Zero temperature should not cause division by zero."""
        from src.agents.evolution import calculate_metropolis_probability
        
        # With T=0, only accept if delta=0
        prob = calculate_metropolis_probability(delta=0.5, t_eff=0.0)
        assert prob == 0.0  # Should be 0, not crash
        
        prob_zero_delta = calculate_metropolis_probability(delta=0.0, t_eff=0.0)
        assert prob_zero_delta == 1.0  # delta=0 always accepted
