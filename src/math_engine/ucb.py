
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
    
    Formula:
    Score = Normalized(V) + c * tau * (sqrt(ln N) / sqrt(p))
    
    Wait, the doc derivation says:
    Exploration Bonus propto sqrt(ln N) / sqrt(p)
    
    Doc 3.2.4.3 says:
    Score(x) = (V - V_min)/(V_max - V_min + eps) + c * tau * (1 / sqrt(p(x)))
    
    Note: The doc formula in 3.2.4.3 omits the sqrt(ln N) term explicitly in the final formula, 
    possibly absorbing it into 'c' or assuming it's part of the standard UCB derivation 
    but the specific implemented formula is: c * tau * (1/sqrt(p)).
    
    However, standard UCB is c * sqrt(ln N / n). 
    Here n ~ p * N. So 1/sqrt(n) ~ 1/sqrt(p*N) = 1/sqrt(p) * 1/sqrt(N).
    
    We will follow the explicit formula in Section 3.2.4.3:
    Bonus = c * tau * (1 / sqrt(p))
    
    Args:
        value: Raw value V(x).
        density: Probability density p(x).
        v_min: Minimum value in population.
        v_max: Maximum value in population.
        count_total: Total population size N (not strictly used in doc formula 3.2.4.3 but commonly in UCB).
                     kept for potential extension.
        tau: Normalized temperature.
        c: Exploration constant.
        epsilon: Stability term for normalization.
        
    Returns:
        UCB score.
    """
    
    # Normalize Value
    v_range = v_max - v_min
    if v_range < epsilon:
        normalized_value = 0.5 # Default middle if range is degenerate
    else:
        normalized_value = (value - v_min) / (v_range + epsilon)
        
    # Exploration Term
    # handle density close to 0
    if density <= 0:
        inv_sqrt_p = 1e6 # Large penalty/bonus? 
        # Low density means High exploration bonus.
        # If density is 0, bonus should be high.
    else:
        inv_sqrt_p = 1.0 / np.sqrt(density)
        
    exploration_bonus = c * tau * inv_sqrt_p
    
    return normalized_value + exploration_bonus

def batch_calculate_ucb(
    values: np.ndarray,
    densities: np.ndarray,
    v_min: float,
    v_max: float,
    tau: float,
    c: float = 1.0
) -> np.ndarray:
    """
    Vectorized calculation of UCB scores.
    """
    # Normalize Values
    epsilon = 1e-5
    v_range = v_max - v_min
    if v_range < epsilon:
        normalized_values = np.full_like(values, 0.5)
    else:
        normalized_values = (values - v_min) / (v_range + epsilon)
        
    # Exploration Terms
    # Avoid div by zero
    safe_densities = np.maximum(densities, 1e-9)
    inv_sqrt_p = 1.0 / np.sqrt(safe_densities)
    
    exploration_bonuses = c * tau * inv_sqrt_p
    
    return normalized_values + exploration_bonuses
