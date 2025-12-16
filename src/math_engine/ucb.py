
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
    c: float = 1.0,
    log_densities: np.ndarray = None
) -> np.ndarray:
    """
    Vectorized UCB calculation using Relative Density in LOG DOMAIN.
    
    Fix for High-Dimensionality:
    In 4096-dim space, raw density p(x) has a tiny magnitude (e.g. 1e-1000) due 
    to volume scaling. Direct exp(log_density) causes underflow to 0.
    
    Solution: 
    Compute relative density directly in log domain:
    log(p_rel) = log_density - log_density_max
    Then: 1/sqrt(p_rel) = exp(-0.5 * log(p_rel)) = exp(-0.5 * (log_density - log_density_max))
    
    Args:
        values: Array of value scores.
        densities: DEPRECATED - kept for backward compatibility, ignored if log_densities provided.
        v_min, v_max: Value range for normalization.
        tau: Normalized temperature.
        c: Exploration constant.
        log_densities: Log-density values (preferred - avoids underflow).
    """
    epsilon = 1e-9
    
    # 1. Normalize Values to [0, 1]
    v_range = v_max - v_min
    if v_range < 1e-5:
        normalized_values = np.full_like(values, 0.5)
    else:
        normalized_values = (values - v_min) / (v_range + 1e-5)
        
    # 2. Relative Density Calculation in LOG DOMAIN
    if log_densities is not None:
        # Use log_densities directly (stable for high-dim)
        log_density_max = np.max(log_densities)
        log_p_rel = log_densities - log_density_max  # log(p_rel) in [-inf, 0]
        
        # Clip to prevent exp overflow: log_p_rel in [-20, 0] => p_rel in [2e-9, 1]
        log_p_rel = np.maximum(log_p_rel, -20.0)
        
        # 1/sqrt(p_rel) = exp(-0.5 * log_p_rel)
        exploration_term = np.exp(-0.5 * log_p_rel)
    else:
        # Legacy path: use densities directly (may underflow in high-dim)
        p_max = np.max(densities)
        if p_max == 0:
            p_max = 1.0
        p_rel = densities / p_max
        p_rel = np.maximum(p_rel, epsilon)
        exploration_term = 1.0 / np.sqrt(p_rel)
    
    # 3. Exploration Term
    # When p_rel = 1 (most explored), term = 1.0 -> Bonus = c * tau
    # When p_rel -> 0 (least explored), term increases (capped by log_p_rel clip)
    return normalized_values + c * tau * exploration_term


