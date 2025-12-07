"""
Test suite for automatic bandwidth estimation (Silverman's Rule).

These tests are written BEFORE implementation (TDD).
Expected to FAIL until estimate_bandwidth is implemented.
"""

import pytest
import numpy as np


class TestSilvermanBandwidth:
    """Tests for the Silverman rule bandwidth estimation."""

    def test_bandwidth_formula_1d(self):
        """Test Silverman's rule formula for 1D data."""
        from src.math_engine.kde import estimate_bandwidth
        
        # 1D data with known standard deviation
        np.random.seed(42)
        data = np.random.randn(100, 1)  # (N, D) format
        
        # Silverman's rule: h = (4 * sigma^5 / (3 * N))^(1/5)
        # For standard normal, sigma ≈ 1
        sigma = np.std(data)
        N = len(data)
        expected = (4 * sigma**5 / (3 * N)) ** 0.2
        
        h = estimate_bandwidth(data)
        
        # Should be close to expected value
        assert abs(h - expected) / expected < 0.1  # Within 10%

    def test_bandwidth_increases_with_variance(self):
        """Higher variance data should have larger bandwidth."""
        from src.math_engine.kde import estimate_bandwidth
        
        np.random.seed(42)
        
        # Low variance data
        low_var_data = np.random.randn(100, 1) * 0.1  # sigma ≈ 0.1
        
        # High variance data
        high_var_data = np.random.randn(100, 1) * 10.0  # sigma ≈ 10
        
        h_low = estimate_bandwidth(low_var_data)
        h_high = estimate_bandwidth(high_var_data)
        
        assert h_high > h_low

    def test_bandwidth_decreases_with_sample_size(self):
        """Larger sample sizes should produce smaller bandwidth."""
        from src.math_engine.kde import estimate_bandwidth
        
        np.random.seed(42)
        
        # Small sample
        small_sample = np.random.randn(50, 1)
        
        # Large sample (from same distribution)
        large_sample = np.random.randn(500, 1)
        
        h_small = estimate_bandwidth(small_sample)
        h_large = estimate_bandwidth(large_sample)
        
        # With same sigma, larger N -> smaller h
        assert h_large < h_small

    def test_bandwidth_handles_multidimensional_data(self):
        """Bandwidth estimation should work for high-dimensional embeddings."""
        from src.math_engine.kde import estimate_bandwidth
        
        np.random.seed(42)
        
        # 768-dim embedding vectors (typical for LLM embeddings)
        high_dim_data = np.random.randn(50, 768)
        
        h = estimate_bandwidth(high_dim_data)
        
        # Should return positive finite value
        assert h > 0
        assert np.isfinite(h)

    def test_bandwidth_with_single_sample_returns_default(self):
        """Single sample should return a reasonable default bandwidth."""
        from src.math_engine.kde import estimate_bandwidth
        
        single_point = np.array([[0.1, 0.2, 0.3]])
        
        h = estimate_bandwidth(single_point)
        
        # Should return some default value, not crash
        assert h > 0
        assert np.isfinite(h)

    def test_bandwidth_with_identical_points(self):
        """Identical points (zero variance) should return minimum bandwidth."""
        from src.math_engine.kde import estimate_bandwidth
        
        # All identical points
        identical_data = np.ones((100, 5)) * 0.5
        
        h = estimate_bandwidth(identical_data)
        
        # Should return a small positive value, not zero or crash
        assert h > 0

    def test_scott_rule_alternative(self):
        """Optionally test Scott's rule as an alternative."""
        from src.math_engine.kde import estimate_bandwidth
        
        np.random.seed(42)
        data = np.random.randn(100, 1)
        
        # Scott's rule: h = N^(-1/(D+4)) * sigma
        # For D=1: h = N^(-1/5) * sigma
        N = len(data)
        D = 1
        sigma = np.std(data)
        scott_h = N ** (-1 / (D + 4)) * sigma
        
        h = estimate_bandwidth(data)
        
        # Silverman and Scott give similar results
        # Just verify our implementation is in the right ballpark
        assert 0.5 * scott_h < h < 2.0 * scott_h


class TestBandwidthIntegration:
    """Tests for bandwidth integration with KDE."""

    def test_auto_bandwidth_used_in_evolution(self):
        """Evolution node should use automatic bandwidth instead of hardcoded value."""
        from src.agents.evolution import evolution_node
        from unittest.mock import patch
        
        state = {
            "problem_state": "Test",
            "strategies": [
                {"id": "s1", "name": "S1", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": list(np.random.randn(768)),
                 "density": None, "log_density": None,
                 "score": 0.5, "status": "active", "trajectory": []},
                {"id": "s2", "name": "S2", "rationale": "R", "assumption": "A",
                 "milestones": [], "embedding": list(np.random.randn(768)),
                 "density": None, "log_density": None,
                 "score": 0.6, "status": "active", "trajectory": []},
            ],
            "research_context": None,
            "spatial_entropy": 0.0,
            "effective_temperature": 0.0,
            "normalized_temperature": 0.0,
            "config": {"beam_width": 5, "t_max": 2.0},
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
        }
        
        with patch("src.agents.evolution.gaussian_kernel_log_density") as mock_kde:
            mock_kde.return_value = np.array([-0.5, -0.6])
            
            with patch("src.agents.evolution.estimate_bandwidth") as mock_bw:
                mock_bw.return_value = 1.5  # Auto-estimated
                
                with patch("src.agents.evolution.embed_text") as mock_embed:
                    mock_embed.return_value = list(np.random.randn(768))
                    
                    evolution_node(state)
                    
                    # Verify estimate_bandwidth was called
                    mock_bw.assert_called_once()
                    
                    # Verify KDE was called with auto-estimated bandwidth
                    kde_call_kwargs = mock_kde.call_args.kwargs
                    assert kde_call_kwargs.get("bandwidth") == 1.5
