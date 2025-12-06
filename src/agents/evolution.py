
import numpy as np
import os
from src.core.state import DeepThinkState, StrategyNode
from src.math_engine.kde import gaussian_kernel_log_density, estimate_density
from src.math_engine.temperature import calculate_effective_temperature, calculate_normalized_temperature
from src.math_engine.ucb import batch_calculate_ucb
from src.embedding_client import embed_text

def evolution_node(state: DeepThinkState) -> DeepThinkState:
    """
    Core Evolutionary Engine Node.
    1. Embeds new strategies.
    2. Calculates Spatial Entropy (via KDE).
    3. Calculates Effective Temperature.
    4. Calculates UCB Scores.
    5. Prunes strategies to maintain Beam Width.
    """
    print("\n[Evolution] Starting evolutionary selection process...")
    
    strategies = state["strategies"]
    
    # 1. Embedding
    # Only embed strategies that don't have embeddings yet
    active_strategies = [s for s in strategies if s["status"] == "active"]
    
    # If no active strategies, return early
    if not active_strategies:
        print("[Evolution] No active strategies to process.")
        return state

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
                strategy["status"] = "pruned_error"

    # Filter out any that failed embedding
    valid_active = [s for s in active_strategies if s.get("embedding") and s["status"] == "active"]
    
    if not valid_active:
        return state

    embeddings = np.array([s["embedding"] for s in valid_active])
    
    # 2. Density Estimation (KDE)
    # Bandwidth: heuristic or fixed. Let's use 1.0 default for now.
    log_densities = gaussian_kernel_log_density(embeddings, bandwidth=1.0)
    densities = np.exp(log_densities)
    
    # Update strategies with density info
    for i, s in enumerate(valid_active):
        s["density"] = float(densities[i])
        s["log_density"] = float(log_densities[i])
        
    # 3. Temperature Calculation
    # We use "Value" V. Here we use the feasibility score from Judge (0.0-1.0).
    # If score is None (skipped judge?), default to 0.5
    values = np.array([s.get("score", 0.5) for s in valid_active])
    
    t_eff = calculate_effective_temperature(values, log_densities)
    
    # T_max parameter from config or default. 
    # Readme: "System maximum allowed temperature". 
    # Let's assume T_max = 2.0 (heuristic).
    t_max = state.get("config", {}).get("t_max", 2.0)
    
    tau = calculate_normalized_temperature(t_eff, t_max)
    
    print(f"  [Metrics] T_eff: {t_eff:.4f}, Tau: {tau:.4f}")
    
    # 4. UCB Calculation
    # c: Exploration constant, default 1.0 (or 1.414)
    c_explore = state.get("config", {}).get("c_explore", 1.0)
    
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
    
    # Update scores
    for i, s in enumerate(valid_active):
        s["score"] = float(ucb_scores[i])
        print(f"  > '{s['name']}' UCB: {ucb_scores[i]:.4f} (Val: {values[i]:.2f}, Dens: {densities[i]:.4f})")
        
    # 5. Pruning (Beam Width)
    k_beam = state.get("config", {}).get("beam_width", 3)
    
    # Sort by UCB descending
    # valid_active is a list of references, so modifying them updates 'strategies'
    # We need to sort valid_active and identify who to prune
    
    sorted_strategies = sorted(valid_active, key=lambda x: x["score"], reverse=True)
    
    kept = sorted_strategies[:k_beam]
    pruned = sorted_strategies[k_beam:]
    
    for s in pruned:
        s["status"] = "pruned_beam"
        s["trajectory"] = s.get("trajectory", []) + ["Pruned by Evolution (Low UCB)"]
        
    print(f"[Evolution] Kept top {len(kept)} strategies. Pruned {len(pruned)}.")
    
    return {
        **state,
        "spatial_entropy": float(-np.mean(log_densities)), # Approximation of entropy
        "effective_temperature": float(t_eff),
        "normalized_temperature": float(tau),
        # 'strategies' is modified in-place since we modified the objects in the list
    }
