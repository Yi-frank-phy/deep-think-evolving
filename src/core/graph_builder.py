
from langgraph.graph import StateGraph, END
from src.core.state import DeepThinkState
from src.agents.architect import strategy_architect_node
from src.agents.judge import judge_node
from src.agents.evolution import evolution_node

from src.agents.researcher import research_node
from src.agents.distiller import distiller_node

def build_deep_think_graph():
    """
    Constructs the Deep Think Evolving StateGraph.
    """
    workflow = StateGraph(DeepThinkState)
    
    # 1. Add Nodes
    workflow.add_node("researcher", research_node)
    workflow.add_node("distiller", distiller_node)
    workflow.add_node("architect", strategy_architect_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("evolution", evolution_node)
    
    # 2. Define Edges
    # Flow: Researcher -> Distiller -> Architect -> Judge -> Evolution -> END
    
    workflow.set_entry_point("researcher")
    
    workflow.add_edge("researcher", "distiller")
    workflow.add_edge("distiller", "architect")
    workflow.add_edge("architect", "judge")
    workflow.add_edge("judge", "evolution")
    workflow.add_edge("evolution", END)
    
    # 3. Compile
    app = workflow.compile()
    return app
