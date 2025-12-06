
import pytest
import numpy as np
from src.math_engine.kde import gaussian_kernel_log_density, estimate_density
from src.math_engine.temperature import calculate_effective_temperature
from src.math_engine.ucb import batch_calculate_ucb

class TestKDE:
    def test_density_1d_cluster(self):
        # 1D cluster around 0
        points = np.array([[0.0], [0.1], [-0.1], [10.0]])
        densities = estimate_density(points, bandwidth=1.0)
        
        # Points near 0 should have higher density than point at 10
        assert densities[0] > densities[3]
        assert densities[1] > densities[3]
        
    def test_log_density_stable(self):
        # Test numerical stability with log density
        points = np.array([[0.0], [10.0]])
        log_densities = gaussian_kernel_log_density(points, bandwidth=0.1)
        
        # log p(0) should be around log(1/2 * (K(0) + K(10))) ~ log(0.5 * K(0))
        # log p(10) same by symmetry
        assert np.isclose(log_densities[0], log_densities[1])
        assert log_densities[0] < 0 # Should be negative prob

class TestTemperature:
    def test_high_temperature(self):
        # Uniform distribution: values and log_p are not correlated
        # Or rather, let's artificially construct uncorrelated data
        values = np.random.rand(100)
        log_p = np.random.rand(100) # Random densities
        
        t_eff = calculate_effective_temperature(values, log_p)
        # Should be very high (or inf)
        # Depending on random noise, covariance might be small but not 0.
        # But generally T_eff should be large.
        assert t_eff > 0.0
        
    def test_linear_relation(self):
        # ln p = 2 * V + C  => 1/T = 2 => T = 0.5
        values = np.linspace(0, 1, 100)
        log_p = 2.0 * values + 0.5
        
        t_eff = calculate_effective_temperature(values, log_p)
        assert np.isclose(t_eff, 0.5, atol=1e-5)
        
class TestUCB:
    def test_ucb_exploration(self):
        # Two points with same value, different density
        # Point A: Dense (p=1.0)
        # Point B: Sparse (p=0.01)
        # B should have higher score if exploration is on
        
        vals = np.array([0.5, 0.5])
        densities = np.array([1.0, 0.01])
        
        scores = batch_calculate_ucb(
            values=vals,
            densities=densities,
            v_min=0,
            v_max=1,
            tau=1.0,
            c=1.0
        )
        
        assert scores[1] > scores[0]

    def test_ucb_exploitation(self):
        # Two points with same density, different value
        vals = np.array([0.9, 0.1])
        densities = np.array([0.5, 0.5])
        
        scores = batch_calculate_ucb(
            values=vals,
            densities=densities,
            v_min=0,
            v_max=1,
            tau=1.0,
            c=1.0
        )
        
        assert scores[0] > scores[1]
