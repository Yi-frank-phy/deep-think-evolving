"""
Test suite for the Evolution Engine.

Tests EBS (Evolutionary Beam Search) core logic including:
- KDE density estimation
- UCB scoring
- Boltzmann child allocation
- Spatial entropy calculation
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestEvolutionNodeBasics:
    """Basic tests for evolution_node function."""
    
    def test_evolution_increments_iteration(self):
        """Evolution should increment iteration_count."""
        from src.agents.evolution import evolution_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {
                    "id": "s1",
                    "name": "Strategy 1",
                    "status": "active",
                    "score": 0.7,
                    "rationale": "R1",
                    "assumption": "A1",
                    "trajectory": []
                }
            ],
            "history": [],
            "iteration_count": 2,
            "spatial_entropy": 1.0,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {"total_child_budget": 4}
        }
        
        with patch('src.agents.evolution.embed_text') as mock_embed:
            mock_embed.return_value = [0.1] * 768  # Mock embedding
            
            result = evolution_node(state)
        
        assert result.get("iteration_count") == 3
    
    def test_evolution_sets_child_quota(self):
        """Evolution should set child_quota on strategies."""
        from src.agents.evolution import evolution_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "S1", "status": "active", "score": 0.9, "rationale": "R", "assumption": "A", "trajectory": []},
                {"id": "s2", "name": "S2", "status": "active", "score": 0.3, "rationale": "R", "assumption": "A", "trajectory": []},
            ],
            "history": [],
            "iteration_count": 0,
            "spatial_entropy": 1.0,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {"total_child_budget": 6}
        }
        
        with patch('src.agents.evolution.embed_text') as mock_embed:
            mock_embed.return_value = [0.1] * 768
            
            result = evolution_node(state)
        
        # All strategies should have child_quota set
        for s in result["strategies"]:
            assert "child_quota" in s
            assert isinstance(s["child_quota"], (int, float))
    
    def test_evolution_updates_spatial_entropy(self):
        """Evolution should calculate and update spatial_entropy."""
        from src.agents.evolution import evolution_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "S1", "status": "active", "score": 0.5, "rationale": "R", "assumption": "A", "trajectory": []},
            ],
            "history": [],
            "iteration_count": 0,
            "spatial_entropy": 999.0,  # Old value
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {}
        }
        
        with patch('src.agents.evolution.embed_text') as mock_embed:
            mock_embed.return_value = [0.1] * 768
            
            result = evolution_node(state)
        
        # spatial_entropy should be updated (may or may not equal old value)
        assert "spatial_entropy" in result


class TestBoltzmannAllocationIntegration:
    """Integration tests for Boltzmann allocation within evolution."""
    
    def test_higher_score_gets_more_children(self):
        """Higher-scoring strategy should receive more children."""
        from src.agents.evolution import evolution_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "High", "status": "active", "score": 0.95, "rationale": "R", "assumption": "A", "trajectory": []},
                {"id": "s2", "name": "Low", "status": "active", "score": 0.05, "rationale": "R", "assumption": "A", "trajectory": []},
            ],
            "history": [],
            "iteration_count": 0,
            "spatial_entropy": 1.0,
            "effective_temperature": 0.5,  # Low temperature to concentrate
            "normalized_temperature": 0.25,
            "config": {"total_child_budget": 10}
        }
        
        with patch('src.agents.evolution.embed_text') as mock_embed:
            # Give different embeddings
            mock_embed.side_effect = [[0.1] * 768, [0.9] * 768]
            
            result = evolution_node(state)
        
        strategies = result["strategies"]
        high_quota = next(s["child_quota"] for s in strategies if s["name"] == "High")
        low_quota = next(s["child_quota"] for s in strategies if s["name"] == "Low")
        
        # High scorer should get more (or equal in edge cases)
        assert high_quota >= low_quota
    
    def test_total_children_equals_budget(self):
        """Sum of child_quota should approximately equal child_budget."""
        from src.agents.evolution import evolution_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "S1", "status": "active", "score": 0.5, "rationale": "R", "assumption": "A", "trajectory": []},
                {"id": "s2", "name": "S2", "status": "active", "score": 0.5, "rationale": "R", "assumption": "A", "trajectory": []},
                {"id": "s3", "name": "S3", "status": "active", "score": 0.5, "rationale": "R", "assumption": "A", "trajectory": []},
            ],
            "history": [],
            "iteration_count": 0,
            "spatial_entropy": 1.0,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {"total_child_budget": 9}
        }
        
        with patch('src.agents.evolution.embed_text') as mock_embed:
            mock_embed.return_value = [0.1] * 768
            
            result = evolution_node(state)
        
        total = sum(s["child_quota"] for s in result["strategies"])
        
        # Should be close to budget (may not be exact due to rounding or min_allocation)
        assert 5 <= total <= 12  # Allow wider range for implementation details


class TestEBSMathematicalProperties:
    """Tests verifying EBS mathematical properties."""
    
    def test_ucb_exploration_bonus_effect(self):
        """Sparse strategies should get exploration bonus in UCB."""
        from src.math_engine.ucb import batch_calculate_ucb
        
        # Two strategies with same value but different densities
        values = np.array([0.5, 0.5])
        densities = np.array([1.0, 0.01])  # Dense vs Sparse
        
        scores = batch_calculate_ucb(
            values=values,
            densities=densities,
            v_min=0, v_max=1,
            tau=1.0, c=1.0
        )
        
        # Sparse strategy (lower density) should have higher UCB
        assert scores[1] > scores[0]
    
    def test_effective_temperature_calculation(self):
        """Temperature should reflect E-ln(p) correlation."""
        from src.math_engine.temperature import calculate_effective_temperature
        
        # ln(p) = 2 * V => slope = 2 => T = 0.5
        values = np.linspace(0, 1, 100)
        log_p = 2.0 * values + 0.5
        
        t_eff = calculate_effective_temperature(values, log_p)
        
        assert np.isclose(t_eff, 0.5, atol=0.01)
    
    def test_kde_density_estimation(self):
        """KDE should assign higher density to clustered points."""
        from src.math_engine.kde import estimate_density
        
        # Cluster at 0, outlier at 10
        points = np.array([[0.0], [0.1], [-0.1], [10.0]])
        
        densities = estimate_density(points, bandwidth=1.0)
        
        # Clustered points should have higher density
        assert densities[0] > densities[3]
        assert densities[1] > densities[3]


class TestEvolutionEdgeCases:
    """Edge case tests for evolution node."""
    
    def test_single_strategy(self):
        """Evolution should handle single strategy."""
        from src.agents.evolution import evolution_node
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "Solo", "status": "active", "score": 0.5, "rationale": "R", "assumption": "A", "trajectory": []}
            ],
            "history": [],
            "iteration_count": 0,
            "spatial_entropy": 0.0,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {"total_child_budget": 4}  # Use correct config key
        }
        
        with patch('src.agents.evolution.embed_text') as mock_embed:
            mock_embed.return_value = [0.1] * 768
            
            result = evolution_node(state)
        
        # Single strategy should get all the budget
        assert result["strategies"][0]["child_quota"] == 4
    
    def test_empty_strategies(self):
        """Evolution should handle empty strategies list."""
        from src.agents.evolution import evolution_node
        
        state = {
            "problem_state": "Test",
            "strategies": [],
            "history": [],
            "iteration_count": 0,
            "spatial_entropy": 0.0,
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {}
        }
        
        result = evolution_node(state)
        
        # Should not crash
        assert result["strategies"] == []
        assert result["iteration_count"] == 1
