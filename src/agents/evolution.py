
import math
import numpy as np
import os
from typing import List, Dict

from src.core.state import DeepThinkState, StrategyNode
from src.math_engine.kde import gaussian_kernel_log_density, estimate_density, estimate_bandwidth, compute_kde_optimized
from src.math_engine.temperature import calculate_effective_temperature, calculate_normalized_temperature
from src.math_engine.ucb import batch_calculate_ucb
from src.embedding_client import embed_text


def calculate_boltzmann_allocation(
    values: np.ndarray,
    t_eff: float,
    total_budget: int,
    min_allocation: int = 0
) -> np.ndarray:
    """
    Calculate child node allocation using pure Boltzmann distribution (Ising model soft pruning).
    
    Formula: n_s = f(C * exp(V_s / T) / Z)
    where Z = sum(exp(V_j / T)) is the partition function.
    
    Rounding rules (分段取整):
    - quota < 1: 四舍五入 (gives low-value strategies fair chance)
    - quota >= 1: 向上取整 (ensures high-value strategies get sufficient resources)
    
    This implements pure Ising model principle without boundary hardcoding:
    - At low T: allocation naturally concentrates on high-value strategies
    - At high T: allocation naturally approaches uniform
    - No artificial cutoffs - let the physics decide
    
    Args:
        values: Array of value scores V for each strategy (typically 0-1 from Judge)
        t_eff: Effective temperature. Higher T -> more uniform allocation.
        total_budget: Total number of children to allocate (approximate, may exceed due to ceiling).
        min_allocation: Minimum children per strategy (default 0 for true soft pruning)
        
    Returns:
        Array of integer child counts for each strategy.
    """
    n = len(values)
    if n == 0:
        return np.array([], dtype=int)
    
    if n == 1:
        return np.array([total_budget], dtype=int)
    
    # Pure Boltzmann distribution: p_s = exp(V_s / T) / Z
    # Use log-sum-exp for numerical stability at ALL temperature ranges
    # Only guard against division by zero, not against extreme temperatures
    safe_t = max(t_eff, 1e-10)  # Only prevent division by zero
    
    log_weights = values / safe_t
    log_weights_max = np.max(log_weights)
    log_Z = log_weights_max + np.log(np.sum(np.exp(log_weights - log_weights_max)))
    
    # Probabilities (log-sum-exp ensures numerical stability)
    probs = np.exp(log_weights - log_Z)
    
    # Raw allocation (continuous)
    raw_allocation = probs * total_budget
    
    # 分段取整 (Piecewise rounding):
    # - quota < 1: 四舍五入 (round) - fair chance for low-value strategies
    # - quota >= 1: 向上取整 (ceil) - ensure high-value strategies get enough
    allocation = np.zeros(n, dtype=int)
    for i, raw in enumerate(raw_allocation):
        if raw < 1.0:
            allocation[i] = int(round(raw))  # 四舍五入
        else:
            allocation[i] = int(np.ceil(raw))  # 向上取整
    
    # Apply minimum allocation if specified
    if min_allocation > 0:
        allocation = np.maximum(allocation, min_allocation)
    
    return allocation



def evolution_node(state: DeepThinkState) -> DeepThinkState:
    """
    Core Evolutionary Engine Node with Soft Pruning.
    
    1. Embeds new strategies.
    2. Calculates Spatial Entropy (via KDE with auto bandwidth).
    3. Calculates Effective Temperature.
    4. Calculates UCB Scores (for ranking/display).
    5. Calculates Boltzmann child allocation (soft pruning - no strategies deleted).
    6. Increments iteration count.
    
    The key change from hard pruning: ALL strategies remain active, but each
    receives a child quota proportional to exp(V/T)/Z. Low-value strategies
    get fewer (possibly zero) children, not deletion.
    """
    print("\n[Evolution] Starting evolutionary selection process...")
    
    # Increment iteration count
    iteration_count = state.get("iteration_count", 0) + 1
    print(f"  [Iteration] {iteration_count}")
    
    strategies = state["strategies"]
    config = state.get("config", {})
    
    # 1. Embedding
    # Only embed strategies that don't have embeddings yet
    active_strategies = [s for s in strategies if s.get("status") == "active"]
    
    # If no active strategies, return early
    if not active_strategies:
        print("[Evolution] No active strategies to process.")
        return {
            **state,
            "iteration_count": iteration_count,
        }

    for strategy in active_strategies:
        if not strategy.get("embedding"):
            text_to_embed = (
                f"Strategy: {strategy['name']}\n"
                f"Rationale: {strategy['rationale']}\n"
                f"Assumption: {strategy['assumption']}"
            )
            print(f"  > Embedding '{strategy['name']}'...")
            vec = embed_text(text_to_embed)
            if vec:
                strategy["embedding"] = vec
            else:
                print(f"  [Warning] Failed to embed '{strategy['name']}'. Marked for pruning.")
                strategy["status"] = "pruned"  # Use standard status value

    # Filter out any that failed embedding
    valid_active = [s for s in active_strategies if s.get("embedding") and s.get("status") == "active"]
    
    if not valid_active:
        return {
            **state,
            "iteration_count": iteration_count,
        }

    embeddings = np.array([s["embedding"] for s in valid_active])
    
    # 2. Density Estimation (KDE) with AUTO BANDWIDTH (Silverman rule)
    # Optimized: Use single pass to compute bandwidth and log densities
    bandwidth, log_densities = compute_kde_optimized(embeddings)
    print(f"  [KDE] Auto bandwidth: {bandwidth:.6f}")
    
    densities = np.exp(log_densities)
    
    # Update strategies with density info
    for i, s in enumerate(valid_active):
        s["density"] = float(densities[i])
        s["log_density"] = float(log_densities[i])
    
    # Calculate Spatial Entropy: S = -mean(log p)
    spatial_entropy = float(-np.mean(log_densities))
    print(f"  [Entropy] Spatial entropy: {spatial_entropy:.4f}")
        
    # 3. Temperature Calculation
    # Use feasibility score from Judge (0.0-1.0) as Value V
    values = np.array([s.get("score", 0.5) for s in valid_active])
    
    t_eff = calculate_effective_temperature(values, log_densities)
    
    # T_max parameter from config (default 2.0 to match LLM temp range)
    t_max = config.get("t_max", 2.0)
    tau = calculate_normalized_temperature(t_eff, t_max)
    
    print(f"  [Temperature] T_eff: {t_eff:.4f}, Tau: {tau:.4f}")
    
    # 4. UCB Calculation (for ranking and display, not for pruning)
    c_explore = config.get("c_explore", 1.0)
    v_min = np.min(values)
    v_max = np.max(values)
    
    ucb_scores = batch_calculate_ucb(
        values=values,
        densities=densities,
        v_min=v_min,
        v_max=v_max,
        tau=tau,
        c=c_explore
    )
    
    # Update UCB scores (for display/ranking)
    for i, s in enumerate(valid_active):
        s["ucb_score"] = float(ucb_scores[i])
    
    # 5. SOFT PRUNING: Boltzmann child allocation
    # Total budget = children_per_parent * num_strategies (from old model)
    # Or use explicit total_child_budget config
    total_budget = config.get("total_child_budget", len(valid_active) * 2)
    
    child_allocation = calculate_boltzmann_allocation(
        values=values,
        t_eff=t_eff,
        total_budget=total_budget,
        min_allocation=config.get("min_children_per_strategy", 0)
    )
    
    # Store allocation in each strategy (propagation node will use this)
    for i, s in enumerate(valid_active):
        s["child_quota"] = int(child_allocation[i])
        s["score"] = float(values[i])  # Keep original value score
        print(f"  > '{s['name']}' Value: {values[i]:.3f}, UCB: {ucb_scores[i]:.4f}, Children: {child_allocation[i]}")
    
    # Count stats
    strategies_with_children = np.sum(child_allocation > 0)
    strategies_without_children = len(valid_active) - strategies_with_children
    
    print(f"[Evolution] Allocated {total_budget} children across {len(valid_active)} strategies "
          f"({strategies_with_children} with children, {strategies_without_children} with 0)")
    
    # Store previous entropy for convergence detection (entropy change rate)
    prev_entropy = state.get("spatial_entropy", None)
    
    return {
        **state,
        "strategies": strategies,  # Explicit return to ensure updated UCB scores are broadcast
        "spatial_entropy": spatial_entropy,
        "prev_spatial_entropy": prev_entropy,  # For convergence detection
        "effective_temperature": float(t_eff),
        "normalized_temperature": float(tau),
        "iteration_count": iteration_count,
        "history": state.get("history", []) + [
            f"Evolution iter {iteration_count}: entropy={spatial_entropy:.3f}, tau={tau:.3f}, "
            f"allocated {total_budget} children to {strategies_with_children}/{len(valid_active)} strategies"
        ]
    }

