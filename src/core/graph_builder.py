
from typing import Literal
from langgraph.graph import StateGraph, END
from src.core.state import DeepThinkState
from src.agents.architect import strategy_architect_node
from src.agents.judge import judge_node
from src.agents.evolution import evolution_node
from src.agents.propagation import propagation_node

from src.agents.researcher import research_node
from src.agents.distiller import distiller_node


def should_continue(state: DeepThinkState) -> Literal["continue", "end"]:
    """
    Determines whether the evolution loop should continue or end.
    
    Convergence conditions (any triggers 'end'):
    1. iteration_count >= max_iterations (default: 10)
    2. spatial_entropy < entropy_threshold (default: 0.1) -> converged
    3. No active strategies remain
    
    Returns:
        "continue" to keep evolving, "end" to terminate.
    """
    config = state.get("config", {})
    max_iterations = config.get("max_iterations", 10)
    entropy_threshold = config.get("entropy_threshold", 0.1)
    
    iteration_count = state.get("iteration_count", 0)
    spatial_entropy = state.get("spatial_entropy", float("inf"))
    strategies = state.get("strategies", [])
    
    # Check if iteration limit reached
    if iteration_count >= max_iterations:
        print(f"[Convergence] Max iterations ({max_iterations}) reached. Ending.")
        return "end"
    
    # Check if entropy converged
    if spatial_entropy < entropy_threshold:
        print(f"[Convergence] Entropy ({spatial_entropy:.4f}) below threshold ({entropy_threshold}). Converged!")
        return "end"
    
    # Check if any active strategies remain
    active_strategies = [s for s in strategies if s.get("status") == "active"]
    if not active_strategies:
        print("[Convergence] No active strategies remain. Ending.")
        return "end"
    
    print(f"[Convergence] Continuing (iter={iteration_count}, entropy={spatial_entropy:.4f})")
    return "continue"


def build_deep_think_graph():
    """
    Constructs the Deep Think Evolving StateGraph with evolution loop.
    
    Flow:
    1. Researcher -> Distiller -> Architect (initial strategy generation)
    2. Judge -> Evolution (first evaluation)
    3. Loop: Evolution -> (should_continue?) -> Propagation -> Judge -> Evolution
    4. When converged: Evolution -> END
    """
    workflow = StateGraph(DeepThinkState)
    
    # 1. Add Nodes
    workflow.add_node("researcher", research_node)
    workflow.add_node("distiller", distiller_node)
    workflow.add_node("architect", strategy_architect_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("evolution", evolution_node)
    workflow.add_node("propagation", propagation_node)
    
    # 2. Define Edges
    # Initial flow: Researcher -> Distiller -> Architect -> Judge -> Evolution
    workflow.set_entry_point("researcher")
    
    workflow.add_edge("researcher", "distiller")
    workflow.add_edge("distiller", "architect")
    workflow.add_edge("architect", "judge")
    workflow.add_edge("judge", "evolution")
    
    # 3. Conditional edge from evolution: loop or end
    workflow.add_conditional_edges(
        "evolution",
        should_continue,
        {
            "continue": "propagation",
            "end": END
        }
    )
    
    # 4. Propagation feeds back into Judge
    workflow.add_edge("propagation", "judge")
    
    # 5. Compile
    app = workflow.compile()
    return app

