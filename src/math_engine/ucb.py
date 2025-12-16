
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
        value: Raw value V(x) - already normalized to [0, 1] by Judge.
        density: Probability density p(x).
        v_min: Minimum value in population (for exploration normalization).
        v_max: Maximum value in population (for exploration normalization).
        count_total: Not used.
        tau: Normalized temperature.
        c: Exploration constant.
        epsilon: Stability term.
        
    Returns:
        UCB score >= value (upper confidence bound property).
    """
    # Score is already in [0, 1] from Judge - do NOT normalize again
    
    # Exploration Term with proper normalization
    if density <= 1e-30:
         inv_sqrt_p = 100.0 # Cap for numerical stability
    else:
         inv_sqrt_p = 1.0 / np.sqrt(density)

    # UCB = score + exploration_bonus
    # exploration_bonus must be non-negative to ensure UCB >= score
    return value + c * tau * inv_sqrt_p

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
    
    UCB = score + c * tau * normalized_exploration
    
    Where:
    - score: Already in [0, 1] from Judge (do NOT normalize)
    - normalized_exploration: 1/sqrt(p_rel), normalized to [1, max_exploration]
    
    This ensures UCB >= score (upper confidence bound property).
    
    Fix for High-Dimensionality:
    Use Relative Density p_rel(x) = p(x) / p_max to eliminate dimension-dependent scaling.
    Then normalize the exploration term to a reasonable range.
    """
    epsilon = 1e-9
    
    # 1. Values are ALREADY in [0,1] from Judge - use directly
    # DO NOT normalize values again!
    
    # 2. Relative Density Calculation
    p_max = np.max(densities)
    
    if p_max == 0:
        p_max = 1.0  # Fallback only if literally zero
        
    p_rel = densities / p_max
    p_rel = np.maximum(p_rel, epsilon)
    
    # 3. Raw exploration term: 1/sqrt(p_rel)
    # When p_rel = 1: exploration = 1
    # When p_rel = epsilon: exploration = 1/sqrt(epsilon) ~= 31623 (too large!)
    raw_exploration = 1.0 / np.sqrt(p_rel)
    
    # 4. Normalize exploration to [0, 1] range
    # This ensures the exploration bonus is comparable to the score scale
    exp_min = np.min(raw_exploration)  # This is 1.0 (when p_rel=1)
    exp_max = np.max(raw_exploration)
    
    if exp_max - exp_min < epsilon:
        # All densities are the same -> uniform exploration bonus
        normalized_exploration = np.ones_like(raw_exploration)
    else:
        # Normalize to [0, 1]: least explored gets 1, most explored gets 0
        normalized_exploration = (raw_exploration - exp_min) / (exp_max - exp_min)
    
    # 5. UCB = score + c * tau * normalized_exploration
    # This guarantees UCB >= score (since normalized_exploration >= 0)
    return values + c * tau * normalized_exploration


