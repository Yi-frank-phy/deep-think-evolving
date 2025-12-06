
import os
import asyncio
from src.core.graph_builder import build_deep_think_graph
from src.core.state import DeepThinkState

async def run_deep_think_graph(problem_statement: str):
    """
    Entry point to run the Deep Think Evolving graph.
    """
    print(f"Initializing Deep Think Graph for problem: {problem_statement[:50]}...")
    
    app = build_deep_think_graph()
    
    initial_state: DeepThinkState = {
        "problem_state": problem_statement,
        "strategies": [],
        "research_context": None,
        "spatial_entropy": 0.0,
        "effective_temperature": 0.0,
        "normalized_temperature": 0.0,
        "config": {
            "t_max": 2.0,
            "c_explore": 1.0,
            "beam_width": 3
        },
        "virtual_filesystem": {},
        "history": ["Graph initialized"]
    }
    
    final_state = await app.ainvoke(initial_state)
    
    print("\n--- Execution Complete ---")
    print(f"Final History: {final_state['history']}")
    print(f"Active Strategies: {len([s for s in final_state['strategies'] if s['status'] == 'active'])}")
    return final_state

if __name__ == "__main__":
    # Test run
    dummy_problem = "How to build a dyson sphere?"
    if os.environ.get("GEMINI_API_KEY"):
         asyncio.run(run_deep_think_graph(dummy_problem))
    else:
        print("GEMINI_API_KEY not set. Skipping execution.")
