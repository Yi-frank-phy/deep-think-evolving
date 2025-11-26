from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

import numpy as np
import pytest

from src import agent_graph
from src.context_manager import SummaryResult


def test_agent_graph_success(tmp_path, monkeypatch):
    # Mock data
    strategies = [
        {
            "strategy_name": "Alpha",
            "rationale": "r1",
            "initial_assumption": "a1",
            "milestones": {"Phase 1": [{"title": "t1", "summary": "s1", "success_criteria": ["c1"]}]},
        },
        {
            "strategy_name": "Beta",
            "rationale": "r2",
            "initial_assumption": "a2",
            "milestones": {},
        },
    ]
    
    embedded_strategies = [
        {**strategies[0], "embedding": [1.0, 0.0]},
        {**strategies[1], "embedding": [0.0, 1.0]},
    ]
    
    similarity_matrix = np.array([[1.0, 0.0], [0.0, 1.0]])
    
    summary_result = SummaryResult(path=Path("fake/path"), text="summary")

    # Mock functions in agent_graph module
    monkeypatch.setattr(agent_graph, "generate_strategic_blueprint", lambda _: strategies)
    monkeypatch.setattr(agent_graph, "embed_strategies", lambda _: embedded_strategies)
    monkeypatch.setattr(agent_graph, "calculate_similarity_matrix", lambda _: similarity_matrix)
    monkeypatch.setattr(agent_graph, "generate_summary", lambda _: summary_result)
    
    # Mock context manager functions
    # We need to capture calls to append_step to verify logic
    append_calls = []
    def mock_append_step(thread_id, payload):
        append_calls.append({"thread_id": thread_id, "payload": payload})
        return Path("fake/history.log")
        
    monkeypatch.setattr(agent_graph, "create_context", lambda _: Path("fake/context"))
    monkeypatch.setattr(agent_graph, "append_step", mock_append_step)

    # Build and run graph
    app = agent_graph.build_graph()
    
    initial_state = {
        "problem_state": "test problem",
        "strategies": [],
        "embedded_strategies": [],
        "similarity_matrix": [],
        "summaries": {},
        "logs": [],
        "thread_registry": [],
    }
    
    result = app.invoke(initial_state)
    
    # Assertions
    assert result["strategies"] == strategies
    assert result["embedded_strategies"] == embedded_strategies
    assert np.array_equal(result["similarity_matrix"], similarity_matrix)
    assert len(result["summaries"]) == 2
    
    # Verify logs were generated
    assert any("Generated 2 strategies" in log for log in result["logs"])
    assert any("Strategies embedded successfully" in log for log in result["logs"])
    
    # Verify context events
    # Strategy init
    init_events = [e for e in append_calls if e["payload"]["event"] == "strategy_initialised"]
    assert len(init_events) == 2
    
    # Embedding events
    embed_events = [e for e in append_calls if e["payload"]["event"] == "embedding_generated"]
    assert len(embed_events) == 2
    
    # Similarity events
    sim_events = [e for e in append_calls if e["payload"]["event"] == "similarity_scores"]
    assert len(sim_events) == 2
