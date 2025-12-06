
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
    
    # Call the legacy function
    # Note: Ensure GEMINI_API_KEY is set in environment
    raw_strategies = generate_strategic_blueprint(problem)
    
    new_strategy_nodes: List[StrategyNode] = []
    
    for raw in raw_strategies:
        node: StrategyNode = {
            "id": str(uuid.uuid4()),
            "name": raw["strategy_name"],
            "rationale": raw["rationale"],
            "assumption": raw["initial_assumption"],
            "milestones": raw["milestones"],
            
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
