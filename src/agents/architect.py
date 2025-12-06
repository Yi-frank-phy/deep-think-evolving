
import uuid
from typing import List, cast

from src.core.state import DeepThinkState, StrategyNode
from src.strategy_architect import generate_strategic_blueprint

def strategy_architect_node(state: DeepThinkState) -> DeepThinkState:
    """
    Node function to generate initial strategic blueprints.
    Wraps the legacy generate_strategic_blueprint function.
    """
    problem = state["problem_state"]
    print(f"\n[Architect] Generating strategies for: {problem[:50]}...")
    
    # Check for Mock Mode or Missing Key
    import os
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key

    if use_mock:
        print("[Architect] Running in MOCK MODE (Key missing or forced).")
        raw_strategies = [
            {"strategy_name": "Mock Strategy A (Solar)", "rationale": "Solar capture is efficient.", "initial_assumption": "Materials available.", "milestones": ["Build", "Launch"]},
            {"strategy_name": "Mock Strategy B (Nuclear)", "rationale": "Nuclear is dense.", "initial_assumption": "Fusion solved.", "milestones": ["Ignite", "Sustain"]},
            {"strategy_name": "Mock Strategy C (Swarm)", "rationale": "Swarm is resilient.", "initial_assumption": "AI control solved.", "milestones": ["Replicate", "Coordination"]}
        ]
    else:
        # Call the legacy function
        # Extract thinking_budget from state config
        thinking_budget = state.get("config", {}).get("thinking_budget", 1024)
        raw_strategies = generate_strategic_blueprint(problem, thinking_budget=thinking_budget)
    
    new_strategy_nodes: List[StrategyNode] = []
    
    for raw in raw_strategies:
        node: StrategyNode = {
            "id": str(uuid.uuid4()),
            "name": raw["strategy_name"],
            "rationale": raw["rationale"],
            "assumption": raw["initial_assumption"],
            "milestones": raw.get("milestones", []), # Safety get
            
            # Initialize metrics
            "embedding": None,
            "density": None,
            "log_density": None,
            "score": 0.0,
            
            "status": "active",
            "trajectory": []
        }
        new_strategy_nodes.append(node)
        
    print(f"[Architect] Generated {len(new_strategy_nodes)} strategies.")
    
    # Update state: append or replace?
    # For now, we assume this is the starting node, so we populate the list.
    # If we want to append, we would do: state["strategies"] + new_strategy_nodes
    # But usually architect runs once at start.
    
    return {
        **state,
        "strategies": new_strategy_nodes,
        "history": state.get("history", []) + [f"Generated {len(new_strategy_nodes)} strategies"]
    }
