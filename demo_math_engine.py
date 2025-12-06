
import numpy as np
import sys
import os
from typing import List, Dict

# Ensure src is in path
sys.path.append(os.getcwd())

from src.math_engine.kde import estimate_density, gaussian_kernel_log_density
from src.math_engine.temperature import calculate_effective_temperature, calculate_normalized_temperature
from src.math_engine.ucb import batch_calculate_ucb

def run_math_demo():
    print("\n=== Deep Think Mathematical Engine Demonstration ===\n")
    print("Scenario: 5 Strategies proposed.")
    print("  - Strategies A, B, C are 'Conventional' (Clustered together)")
    print("  - Strategy D is 'Novel' (Outlier, far from others)")
    print("  - Strategy E is 'noise' (Very far, low value)")
    
    # 1. Setup Synthetic Embeddings (2D for easy visualization thought)
    # A, B, C clustered around [0, 0]
    # D at [5, 5]
    # E at [-5, 5]
    
    embeddings = np.array([
        [0.0, 0.0],   # A
        [0.1, 0.1],   # B
        [-0.1, 0.0],  # C
        [2.0, 2.0],   # D (Novel)
        [-2.0, 2.0]   # E (Noise/Different)
    ])
    
    names = ["Strat A (Standard)", "Strat B (Standard)", "Strat C (Standard)", "Strat D (Novel)", "Strat E (Alien)"]
    
    # 2. Setup Base "Judge" Scores (Feasibility/Value)
    # Let's say Conventional ones are 'safe' and score okay (0.6).
    # Novel one might be risky/rough, score lower initially (0.4).
    # Alien is pure junk (0.1).
    values = np.array([0.7, 0.65, 0.68, 0.45, 0.1])
    
    print(f"{'Name':<20} | {'Vector':<15} | {'Base Score':<10}")
    print("-" * 55)
    for i in range(len(names)):
        print(f"{names[i]:<20} | {str(embeddings[i]):<15} | {values[i]:.2f}")
    
    # 3. Calculate Density (KDE)
    print("\n--- Step 1: Kernel Density Estimation (KDE) ---")
    log_densities = gaussian_kernel_log_density(embeddings, bandwidth=1.0)
    densities = np.exp(log_densities)
    
    print(f"{'Name':<20} | {'Density p(x)':<12} | {'Log Density':<12}")
    print("-" * 55)
    for i in range(len(names)):
        print(f"{names[i]:<20} | {densities[i]:.4f}       | {log_densities[i]:.4f}")
        
    print("\n[Observation]: 'Standard' strategies have HIGH density (crowded). 'Novel' has LOW density.")
    
    # 4. Calculate Temperature
    print("\n--- Step 2: System Temperature (Linearized) ---")
    t_eff = calculate_effective_temperature(values, log_densities)
    t_max = 2.0
    tau = calculate_normalized_temperature(t_eff, t_max)
    
    print(f"Effective Temperature (T_eff): {t_eff:.4f}")
    print(f"Max Allowed Temp (T_max):      {t_max:.2f}")
    print(f"Normalized Temp (Tau):         {tau:.4f}")
    
    # 5. Calculate UCB Scores
    print("\n--- Step 3: Dynamic UCB Scoring ---")
    print("Formula: Score = Norm(Value) + c * Tau * (1 / sqrt(p))")
    
    ucb_scores = batch_calculate_ucb(
        values=values,
        densities=densities,
        v_min=np.min(values),
        v_max=np.max(values),
        tau=tau,
        c=1.0 # Exploration Constant
    )
    
    print(f"{'Name':<20} | {'Base(Norm)':<10} | {'Exploration Bonus':<17} | {'FINAL UCB':<10}")
    print("-" * 75)
    
    # Re-normalize values for display to match UCB internal logic
    v_min, v_max = np.min(values), np.max(values)
    norm_values = (values - v_min) / (v_max - v_min + 1e-5)
    
    for i in range(len(names)):
        bonus = ucb_scores[i] - norm_values[i]
        print(f"{names[i]:<20} | {norm_values[i]:.4f}     | {bonus:.4f}            | {ucb_scores[i]:.4f}")
        
    # 6. Ranking & Pruning
    print("\n--- Step 4: Evolution Selection (Top 3) ---")
    ranked_indices = np.argsort(ucb_scores)[::-1]
    
    print("Final Ranking:")
    for rank, idx in enumerate(ranked_indices, 1):
        status = "KEPT" if rank <= 3 else "PRUNED"
        print(f"#{rank}: {names[idx]} (Score: {ucb_scores[idx]:.4f}) -> {status}")
        
    print("\n=== End of Demonstration ===")

if __name__ == "__main__":
    run_math_demo()
