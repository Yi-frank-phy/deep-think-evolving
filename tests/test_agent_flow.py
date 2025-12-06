
import pytest
from unittest.mock import MagicMock, patch
from src.core.graph_builder import build_deep_think_graph
from src.core.state import DeepThinkState

@pytest.mark.asyncio
async def test_agent_flow_mocked():
    """
    Verifies the graph flow from Architect -> Judge -> Evolution
    using mocked LLM responses to avoid API calls and ensuring deterministic logic.
    """
    print("\n--- Starting End-to-End Graph Flow Test (Mocked) ---")

    # 1. Mock Architect Response
    mock_strategies = [
        {"id": "strat-1", "name": "Strategy A", "rationale": "Test Rationale A", "status": "active"},
        {"id": "strat-2", "name": "Strategy B", "rationale": "Test Rationale B", "status": "active"}
    ]
    
    # 2. Mock Judge Response (Feasibility Scores)
    # Judge usually updates 'score'
    def mock_judge_side_effect(state):
        strat_nodes = state["strategies"]
        for s in strat_nodes:
            s["score"] = 8.5 # Arbitrary high score to survive
        state["history"].append("Judge Mock Executed")
        return state

    # 3. Mock Evolution Components (Embedding, UCB)
    # We need to mock the external calls inside evolution_node
    
    with patch("src.agents.architect.generate_strategic_blueprint") as mock_gen_blueprint, \
         patch("src.agents.judge.judge_node", side_effect=mock_judge_side_effect) as mock_judge, \
         patch("src.agents.evolution.embed_text") as mock_embed, \
         patch("src.agents.evolution.estimate_density") as mock_est_density, \
         patch("src.agents.evolution.batch_calculate_ucb") as mock_calc_ucb:

        # Setup Mocks
        mock_gen_blueprint.return_value = {
            "strategies": mock_strategies,
            "metrics": {}
        }
        
        # Evolution Mocks
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]] # Fake embeddings
        mock_est_density.return_value = [0.5, 0.5] # Fake densities
        mock_calc_ucb.return_value = [0.9, 0.8] # Fake UCB scores

        # Build Graph
        app = build_deep_think_graph()
        
        initial_state: DeepThinkState = {
            "problem_state": "Test Problem",
            "strategies": [],
            "research_context": None,
            "spatial_entropy": 0.0,
            "effective_temperature": 0.0,
            "normalized_temperature": 0.0,
            "config": {
                "t_max": 2.0,
                "c_explore": 1.0,
                "beam_width": 2
            },
            "virtual_filesystem": {},
            "history": []
        }

        # Run Graph
        # Note: We likely need to mock 'researcher' and 'distiller' too if they are entry points
        # OR we can just test the sub-graph. 
        # But 'build_deep_think_graph' connects Researcher -> Distiller -> Architect.
        # So we should mock them too to pass through.
        
        with patch("src.agents.researcher.research_node", return_value=initial_state) as mock_research, \
             patch("src.agents.distiller.distiller_node", return_value=initial_state) as mock_distill:
             
             # Adjust mock to chain state correctly if needed, or just let them return input state
             # Actually, if they return input state, the flow continues.
             
             final_state = await app.ainvoke(initial_state)

        # Assertions
        print(f"Final History: {final_state['history']}")
        
        # 1. Did Architect run?
        assert len(final_state["strategies"]) == 2
        assert final_state["strategies"][0]["name"] == "Strategy A"
        
        # 2. Did Judge run? (Check for score update or history)
        # Our mock judge added a history item
        assert "Judge Mock Executed" in final_state["history"]
        assert final_state["strategies"][0]["score"] == 8.5
        
        # 3. Did Evolution run? (Check for embeddings presence if our mock injected it? 
        # Actually our mock_drive 'evolution_node' logic usually updates state.
        # But here we mocked the INTERNAL functions of evolution node, not the node itself.
        # So evolution_node logic SHOULD run and populate state metrics.
        
        # If evolution_node calls mock_embed, mock_est_density...
        mock_embed.assert_called()
        mock_calc_ucb.assert_called()
        
        print("[PASS] End-to-End Flow Verified")

if __name__ == "__main__":
    # Manually run async for quick debug if needed
    import asyncio
    asyncio.run(test_agent_flow_mocked())
