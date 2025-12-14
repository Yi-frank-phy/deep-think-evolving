
import numpy as np

def calculate_ucb_score(
    value: float,
    density: float,
    v_min: float,
    v_max: float,
    count_total: int,
    tau: float,
    c: float = 1.0,
    epsilon: float = 1e-5
) -> float:
    """
    Calculates the Dynamic Normalized UCB score for a single item.
    
    Args:
        value: Raw value V(x).
        density: Probability density p(x).
        v_min: Minimum value in population.
        v_max: Maximum value in population.
        count_total: Not used.
        tau: Normalized temperature.
        c: Exploration constant.
        epsilon: Stability term.
        
    Returns:
        UCB score.
    """
    # 1. Normalize Value to [0, 1]
    v_range = v_max - v_min
    if v_range < epsilon:
        normalized_value = 0.5
    else:
        normalized_value = (value - v_min) / (v_range + epsilon)
        
    # 2. Exploration Term with dimensionality correction
    # Single item calculation lacks context of p_max, so we assume
    # the caller has already normalized density or we use raw (danger of explosion).
    # For safety in single-item calls, we clamp, but batch mode is preferred.
    if density <= 1e-30:
         inv_sqrt_p = 100.0 # Cap for numerical stability
    else:
         inv_sqrt_p = 1.0 / np.sqrt(density)

    # Note: Single item calculation is inherently risky for high-dim scaling
    # without p_max context. Batch calculation is strongly recommended.
    return normalized_value + c * tau * inv_sqrt_p

def batch_calculate_ucb(
    values: np.ndarray,
    densities: np.ndarray,
    v_min: float,
    v_max: float,
    tau: float,
    c: float = 1.0
) -> np.ndarray:
    """
    Vectorized UCB calculation using Relative Density.
    
    Fix for High-Dimensionality:
    In 4096-dim space, raw density p(x) has a tiny magnitude (e.g. 1e-1000) due 
    to volume scaling. This causes 1/sqrt(p) to explode.
    
    Solution: 
    Use Relative Density p_rel(x) = p(x) / p_max.
    Exploration = c * tau * (1 / sqrt(p_rel))
    
    This preserves the exact shape/physics of the distribution derived from 
    Gaussian kernels, but eliminates the dimension-dependent constant factor.
    """
    epsilon = 1e-9
    
    # 1. Normalize Values to [0, 1]
    v_range = v_max - v_min
    if v_range < 1e-5:
        normalized_values = np.full_like(values, 0.5)
    else:
        normalized_values = (values - v_min) / (v_range + 1e-5)
        
    # 2. Relative Density Calculation
    # p_max captures the "scale" of the current probability landscape
    # In high-dim space, p_max can be extremely small (e.g. 1e-1000) - this is NORMAL
    p_max = np.max(densities)
    
    # Only guard against actual zero (not small values)
    if p_max == 0:
        p_max = 1.0  # Fallback only if literally zero
        
    # p_rel will be in (0, 1]
    # We use stable division
    p_rel = densities / p_max
    
    # Clip small values to prevent 1/sqrt(0)
    p_rel = np.maximum(p_rel, epsilon)
    
    # 3. Exploration Term
    # When p_rel = 1 (most explored), term = 1.0 -> Bonus = c * tau
    # When p_rel -> 0 (least explored), term increases
    exploration_term = 1.0 / np.sqrt(p_rel)
    
    return normalized_values + c * tau * exploration_term


