
import numpy as np

def calculate_effective_temperature(
    values: np.ndarray, 
    log_densities: np.ndarray
) -> float:
    """
    Calculates the Effective Temperature (T_eff) using the slope of the 
    Energy-LogProbability relation.
    
    Theory: ln p(v) = (1/T) * v + C
    We estimate 1/T using linear regression slope k. 
    T_eff = 1 / |k| = | Var(V) / Cov(V, ln p) |
    
    Args:
        values: (N,) array of value scores (V).
        log_densities: (N,) array of log density estimates (ln p).
        
    Returns:
        Estimated effective temperature T_eff. 
        Returns float('inf') if covariance is effectively zero (flat distribution).
    """
    if len(values) != len(log_densities):
        raise ValueError("Values and log_densities must have the same length.")
    
    if len(values) < 2:
        return float('inf') # Cannot estimate variance with < 2 samples
        
    # Covariance matrix between V and ln p
    # cov_matrix = [[Var(V), Cov(V, ln p)], [Cov(ln p, V), Var(ln p)]]
    cov_matrix = np.cov(values, log_densities)
    
    var_v = cov_matrix[0, 0]
    cov_v_logp = cov_matrix[0, 1]
    
    if np.abs(cov_v_logp) < 1e-12:
        return float('inf') # Slope is 0 -> T is infinite (or undefined)
        
    # k = Cov(V, ln p) / Var(V) ? No, actually:
    # If y = kx + b (y=ln p, x=V)
    # k = Cov(x, y) / Var(x) = Cov(V, ln p) / Var(V)
    # T = 1/k = Var(V) / Cov(V, ln p)
    
    t_eff = np.abs(var_v / cov_v_logp)
    
    return float(t_eff)

def calculate_normalized_temperature(
    t_eff: float, 
    t_max: float = 1.0
) -> float:
    """
    Returns normalized temperature tau = T_eff / T_max.
    """
    if t_max <= 0:
        raise ValueError("T_max must be positive.")
    return t_eff / t_max
