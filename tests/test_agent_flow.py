
import os
import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.skip(reason="Needs rewrite for new Agent architecture with proper module isolation")
@pytest.mark.asyncio
async def test_agent_flow_mocked():
    """
    Verifies the graph flow using mocked LLM responses to avoid API calls 
    and ensuring deterministic logic.
    
    Updated for new Agent architecture:
    - Uses strategy_architect_node (which now wraps strategy_generator_node)
    - Mocks USE_MOCK_AGENTS environment variable for deterministic behavior
    """
    print("\n--- Starting End-to-End Graph Flow Test (Mocked) ---")

    # Set environment variable BEFORE any imports that might use it
    os.environ["USE_MOCK_AGENTS"] = "true"
    
    try:
        # Import AFTER setting mock mode
        from src.core.graph_builder import build_deep_think_graph
        from src.core.state import DeepThinkState
        
        # Build Graph
        app = build_deep_think_graph()
        
        initial_state: DeepThinkState = {
            "problem_state": "Test Problem",
            "strategies": [],
            "research_context": None,
            "research_status": None,
            "subtasks": None,
            "information_needs": None,
            "spatial_entropy": 0.0,
            "effective_temperature": 0.0,
            "normalized_temperature": 0.0,
            "config": {
                "t_max": 2.0,
                "c_explore": 1.0,
                "beam_width": 2,
                "max_iterations": 1  # Limit iterations for test
            },
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
            "judge_context": None,
            "architect_decisions": None
        }

        # Run Graph
        final_state = await app.ainvoke(initial_state)

        # Assertions
        print(f"Final History: {final_state['history']}")
        
        # 1. Did Architect (or StrategyGenerator in new flow) create strategies?
        assert len(final_state["strategies"]) >= 2, "Should have generated at least 2 strategies"
        
        # 2. Did strategies get processed through the pipeline?
        # Check that strategies have names
        for s in final_state["strategies"]:
            assert "name" in s, "Strategy should have a name"
            assert s["name"], "Strategy name should not be empty"
        
        # 3. Check history has meaningful entries
        assert len(final_state["history"]) > 0, "Should have history entries"
        
        print("[PASS] End-to-End Flow Verified")
    
    finally:
        # Cleanup: remove the mock environment variable
        os.environ.pop("USE_MOCK_AGENTS", None)

if __name__ == "__main__":
    # Manually run async for quick debug if needed
    import asyncio
    asyncio.run(test_agent_flow_mocked())

