"""
Test suite for Boltzmann soft pruning (replaces Metropolis hard pruning tests).

Tests the child allocation based on Boltzmann distribution: n_s ∝ exp(V_s/T)/Z
"""

import pytest
import numpy as np
import math


class TestBoltzmannAllocation:
    """Tests for the Boltzmann distribution child allocation."""

    def test_allocation_sums_to_budget(self):
        """Total allocated children should equal the budget."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        values = np.array([0.9, 0.7, 0.5, 0.3])
        t_eff = 1.0
        total_budget = 10
        
        allocation = calculate_boltzmann_allocation(values, t_eff, total_budget)
        
        assert np.sum(allocation) == total_budget

    def test_higher_value_gets_more_children(self):
        """Higher value strategies should receive more children."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        values = np.array([0.9, 0.5, 0.1])
        t_eff = 1.0
        total_budget = 10
        
        allocation = calculate_boltzmann_allocation(values, t_eff, total_budget)
        
        # Highest value should get most children
        assert allocation[0] >= allocation[1]
        assert allocation[1] >= allocation[2]

    def test_low_temperature_concentrates_allocation(self):
        """At low T, almost all children go to highest value strategy."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        values = np.array([0.9, 0.5, 0.1])
        t_eff = 0.001  # Very low T
        total_budget = 10
        
        allocation = calculate_boltzmann_allocation(values, t_eff, total_budget)
        
        # Best strategy should get almost all
        assert allocation[0] >= 9

    def test_high_temperature_uniform_allocation(self):
        """At high T, allocation approaches uniform distribution."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        values = np.array([0.9, 0.5, 0.1])
        t_eff = 1e7  # Very high T
        total_budget = 12
        
        allocation = calculate_boltzmann_allocation(values, t_eff, total_budget)
        
        # Should be roughly uniform: each gets ~4
        for a in allocation:
            assert 3 <= a <= 5

    def test_zero_temperature_all_to_best(self):
        """At T=0, all children go to best strategy."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        values = np.array([0.5, 0.9, 0.3])  # Best is index 1
        t_eff = 0.0
        total_budget = 10
        
        allocation = calculate_boltzmann_allocation(values, t_eff, total_budget)
        
        assert allocation[1] == 10
        assert allocation[0] == 0
        assert allocation[2] == 0

    def test_single_strategy_gets_all(self):
        """Single strategy should get entire budget."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        values = np.array([0.5])
        t_eff = 1.0
        total_budget = 5
        
        allocation = calculate_boltzmann_allocation(values, t_eff, total_budget)
        
        assert len(allocation) == 1
        assert allocation[0] == 5

    def test_empty_values_returns_empty(self):
        """Empty input should return empty allocation."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        values = np.array([])
        t_eff = 1.0
        total_budget = 10
        
        allocation = calculate_boltzmann_allocation(values, t_eff, total_budget)
        
        assert len(allocation) == 0

    def test_minimum_allocation_enforced(self):
        """When min_allocation is set, all strategies get at least that many."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        values = np.array([0.9, 0.1])
        t_eff = 0.01  # Low T would normally give all to best
        total_budget = 10
        min_alloc = 2
        
        allocation = calculate_boltzmann_allocation(
            values, t_eff, total_budget, min_allocation=min_alloc
        )
        
        # Each should have at least min_allocation
        assert allocation[0] >= min_alloc
        assert allocation[1] >= min_alloc


class TestBoltzmannPhysics:
    """Tests verifying Boltzmann distribution physics."""

    def test_allocation_ratio_follows_boltzmann(self):
        """Ratio n_i/n_j should equal exp((V_i - V_j)/T)."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        v1, v2 = 0.8, 0.5
        values = np.array([v1, v2])
        t_eff = 0.5
        total_budget = 100  # Large budget for stable ratio
        
        allocation = calculate_boltzmann_allocation(values, t_eff, total_budget)
        
        # Theoretical ratio
        expected_ratio = math.exp((v1 - v2) / t_eff)
        
        # Actual ratio (avoid div by zero)
        if allocation[1] > 0:
            actual_ratio = allocation[0] / allocation[1]
            # Allow some tolerance due to rounding
            assert abs(actual_ratio - expected_ratio) / expected_ratio < 0.2

    def test_partition_function_normalizes(self):
        """Probabilities should sum to 1 (normalization by Z)."""
        from src.agents.evolution import calculate_boltzmann_allocation
        
        values = np.array([0.9, 0.7, 0.5, 0.3, 0.1])
        t_eff = 1.0
        total_budget = 100
        
        allocation = calculate_boltzmann_allocation(values, t_eff, total_budget)
        
        # Allocation is proportional to probability, so sum = budget
        assert np.sum(allocation) == total_budget


class TestSoftPruningInEvolution:
    """Tests for soft pruning integration in evolution node."""

    def test_evolution_sets_child_quota(self):
        """Evolution node should set child_quota on each strategy."""
        from src.agents.evolution import evolution_node
        from unittest.mock import patch
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "S1", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1, 0.2], "density": None, "log_density": None,
                 "score": 0.8, "status": "active", "trajectory": []},
                {"id": "s2", "name": "S2", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.3, 0.4], "density": None, "log_density": None,
                 "score": 0.4, "status": "active", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.0,
            "effective_temperature": 0.0,
            "normalized_temperature": 0.0,
            "config": {"total_child_budget": 10},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.evolution.embed_text") as mock_embed:
            mock_embed.return_value = [0.1, 0.2]
            
            new_state = evolution_node(state)
        
        # Both strategies should have child_quota set
        for s in new_state["strategies"]:
            if s["status"] == "active":
                assert "child_quota" in s
                assert isinstance(s["child_quota"], int)
        
        # Total quota should match budget
        total_quota = sum(s.get("child_quota", 0) for s in new_state["strategies"])
        assert total_quota == 10

    def test_no_strategies_marked_pruned(self):
        """Soft pruning should NOT mark any strategies as 'pruned_beam'."""
        from src.agents.evolution import evolution_node
        from unittest.mock import patch
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "S1", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.1, 0.2], "density": None, "log_density": None,
                 "score": 0.9, "status": "active", "trajectory": []},
                {"id": "s2", "name": "S2", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": [0.3, 0.4], "density": None, "log_density": None,
                 "score": 0.1, "status": "active", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.0,
            "effective_temperature": 0.0,
            "normalized_temperature": 0.0,
            "config": {"total_child_budget": 5},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.evolution.embed_text") as mock_embed:
            mock_embed.return_value = [0.1, 0.2]
            
            new_state = evolution_node(state)
        
        # No strategy should have status 'pruned_beam'
        for s in new_state["strategies"]:
            assert s["status"] != "pruned_beam"
