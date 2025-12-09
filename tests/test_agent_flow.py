"""
Test Agent Flow - 测试新的 Agent 架构流程

测试新的 Deep Think Evolving Agent 流程：
Phase 1: TaskDecomposer → Researcher → StrategyGenerator
Phase 2: DistillerForJudge → Judge → Evolution
Phase 3: ArchitectScheduler → Executor → (循环)
"""

import os
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


# ============================================================================
# Unit Tests for Individual Agents (Mock Mode)
# ============================================================================

class TestTaskDecomposerAgent:
    """Tests for the TaskDecomposer agent."""
    
    def test_task_decomposer_returns_subtasks(self):
        """TaskDecomposer should return subtasks and information needs."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        try:
            from src.agents.task_decomposer import task_decomposer_node
            
            state = {
                "problem_state": "如何设计一个高效的分布式系统？",
                "history": []
            }
            
            result = task_decomposer_node(state)
            
            # Should have subtasks
            assert "subtasks" in result
            assert len(result["subtasks"]) > 0
            
            # Should have information needs
            assert "information_needs" in result
            assert len(result["information_needs"]) > 0
            
            # Should update history
            assert len(result["history"]) > 0
            
        finally:
            os.environ.pop("USE_MOCK_AGENTS", None)


class TestResearcherAgent:
    """Tests for the Researcher agent."""
    
    def test_researcher_returns_context_and_status(self):
        """Researcher should return research_context and research_status."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        try:
            from src.agents.researcher import research_node
            
            state = {
                "problem_state": "测试问题",
                "information_needs": [
                    {"topic": "测试主题", "type": "factual", "priority": 5}
                ],
                "config": {"max_research_iterations": 3},
                "history": []
            }
            
            result = research_node(state)
            
            # Should have research context
            assert "research_context" in result
            assert result["research_context"] is not None
            
            # Should have status
            assert "research_status" in result
            assert result["research_status"] in ["sufficient", "insufficient"]
            
            # Should track iteration
            assert "research_iteration" in result
            assert result["research_iteration"] == 1
            
        finally:
            os.environ.pop("USE_MOCK_AGENTS", None)


class TestStrategyGeneratorAgent:
    """Tests for the StrategyGenerator agent."""
    
    def test_strategy_generator_creates_strategies(self):
        """StrategyGenerator should create initial strategies."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        try:
            from src.agents.strategy_generator import strategy_generator_node
            
            state = {
                "problem_state": "测试问题",
                "research_context": "背景知识",
                "subtasks": ["子任务1", "子任务2"],
                "history": []
            }
            
            result = strategy_generator_node(state)
            
            # Should have strategies
            assert "strategies" in result
            assert len(result["strategies"]) >= 2
            
            # Each strategy should have required fields
            for s in result["strategies"]:
                assert "id" in s
                assert "name" in s
                assert "rationale" in s
                assert "status" in s
                assert s["status"] == "active"
            
        finally:
            os.environ.pop("USE_MOCK_AGENTS", None)


class TestArchitectSchedulerAgent:
    """Tests for the ArchitectScheduler agent."""
    
    def test_architect_scheduler_creates_decisions(self):
        """ArchitectScheduler should create execution decisions."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        try:
            from src.agents.architect import architect_scheduler_node
            
            state = {
                "problem_state": "测试问题",
                "strategies": [
                    {
                        "id": "test-1",
                        "name": "策略A",
                        "rationale": "理由A",
                        "assumption": "假设A",
                        "status": "active",
                        "score": 0.8,
                        "ucb_score": 0.9,
                        "child_quota": 2
                    },
                    {
                        "id": "test-2", 
                        "name": "策略B",
                        "rationale": "理由B",
                        "assumption": "假设B",
                        "status": "active",
                        "score": 0.6,
                        "ucb_score": 0.7,
                        "child_quota": 1
                    }
                ],
                "history": []
            }
            
            result = architect_scheduler_node(state)
            
            # Should have decisions
            assert "architect_decisions" in result
            assert len(result["architect_decisions"]) > 0
            
            # Each decision should have required fields
            for d in result["architect_decisions"]:
                assert "strategy_id" in d
                assert "executor_instruction" in d
            
        finally:
            os.environ.pop("USE_MOCK_AGENTS", None)


class TestExecutorAgent:
    """Tests for the Executor agent."""
    
    def test_executor_processes_decisions(self):
        """Executor should process architect decisions."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        try:
            from src.agents.executor import executor_node
            
            state = {
                "problem_state": "测试问题",
                "strategies": [
                    {
                        "id": "test-1",
                        "name": "策略A",
                        "rationale": "理由A",
                        "assumption": "假设A",
                        "status": "active",
                        "trajectory": []
                    }
                ],
                "architect_decisions": [
                    {
                        "strategy_id": "test-1",
                        "executor_instruction": "探索此策略",
                        "context_injection": ""
                    }
                ],
                "history": []
            }
            
            result = executor_node(state)
            
            # Decisions should be cleared after execution
            assert result["architect_decisions"] == []
            
            # Strategy trajectory should be updated
            assert len(result["strategies"][0]["trajectory"]) > 0
            
        finally:
            os.environ.pop("USE_MOCK_AGENTS", None)


class TestJudgeAgent:
    """Tests for the Judge agent (pure scoring, no hard pruning)."""
    
    def test_judge_scores_without_pruning(self):
        """Judge should score strategies without hard pruning."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        try:
            from src.agents.judge import judge_node
            
            state = {
                "problem_state": "测试问题",
                "strategies": [
                    {
                        "id": "test-1",
                        "name": "策略A",
                        "rationale": "理由A",
                        "assumption": "假设A",
                        "status": "active",
                        "trajectory": []
                    }
                ],
                "judge_context": "评估上下文",
                "history": [],
                "config": {}
            }
            
            result = judge_node(state)
            
            # Strategy should have score
            assert "score" in result["strategies"][0]
            
            # Strategy should NOT be pruned (pure Ising model)
            assert result["strategies"][0]["status"] == "active"
            
        finally:
            os.environ.pop("USE_MOCK_AGENTS", None)


# ============================================================================
# Integration Tests for Graph Flow
# ============================================================================

class TestGraphFlow:
    """Integration tests for the full graph flow."""
    
    def test_graph_compiles_successfully(self):
        """Graph should compile without errors."""
        from src.core.graph_builder import build_deep_think_graph
        
        app = build_deep_think_graph()
        assert app is not None
        
    def test_graph_has_new_nodes(self):
        """Graph should contain all new agent nodes."""
        from src.core.graph_builder import build_deep_think_graph
        
        app = build_deep_think_graph()
        graph = app.get_graph()
        
        # Get all node names (graph.nodes is a dict)
        node_names = list(graph.nodes.keys())
        
        # Check new nodes exist
        expected_nodes = [
            "task_decomposer",
            "researcher", 
            "strategy_generator",
            "distiller_for_judge",
            "judge",
            "evolution",
            "architect_scheduler",
            "executor"
        ]
        
        for node in expected_nodes:
            assert node in node_names, f"Node '{node}' should exist in graph"
    
    def test_graph_entry_point_is_task_decomposer(self):
        """Graph entry point should be task_decomposer."""
        from src.core.graph_builder import build_deep_think_graph
        
        app = build_deep_think_graph()
        graph = app.get_graph()
        
        # Find entry point (node with edge from __start__)
        start_edges = [e for e in graph.edges if e.source == "__start__"]
        
        assert len(start_edges) > 0
        assert start_edges[0].target == "task_decomposer"


class TestResearchLoop:
    """Tests for the research continuation loop."""
    
    def test_should_research_continue_proceeds_when_sufficient(self):
        """should_research_continue returns 'proceed' when info sufficient."""
        from src.core.graph_builder import should_research_continue
        
        state = {
            "research_status": "sufficient",
            "research_iteration": 1,
            "config": {"max_research_iterations": 3}
        }
        
        result = should_research_continue(state)
        assert result == "proceed"
    
    def test_should_research_continue_loops_when_insufficient(self):
        """should_research_continue returns 'research_more' when insufficient."""
        from src.core.graph_builder import should_research_continue
        
        state = {
            "research_status": "insufficient",
            "research_iteration": 1,
            "config": {"max_research_iterations": 3}
        }
        
        result = should_research_continue(state)
        assert result == "research_more"
    
    def test_should_research_continue_proceeds_at_max_iterations(self):
        """should_research_continue proceeds when max iterations reached."""
        from src.core.graph_builder import should_research_continue
        
        state = {
            "research_status": "insufficient",  # Still insufficient
            "research_iteration": 3,  # But at max
            "config": {"max_research_iterations": 3}
        }
        
        result = should_research_continue(state)
        assert result == "proceed"


class TestDistillerDynamicTrigger:
    """Tests for Distiller's dynamic triggering."""
    
    def test_estimate_token_count(self):
        """estimate_token_count should estimate correctly."""
        from src.agents.distiller import estimate_token_count
        
        state = {
            "problem_state": "这是一个测试问题" * 100,  # ~800 chars
            "research_context": "研究背景" * 100,  # ~400 chars
            "judge_context": None,
            "strategies": [],
            "history": []
        }
        
        tokens = estimate_token_count(state)
        
        # Should be roughly (800 + 400) / 4 = 300 tokens
        assert 200 < tokens < 400
    
    def test_should_distill_returns_true_when_over_threshold(self):
        """should_distill returns True when context exceeds threshold."""
        from src.agents.distiller import should_distill
        
        state = {
            "problem_state": "x" * 20000,  # Large context
            "research_context": "y" * 20000,
            "judge_context": None,
            "strategies": [],
            "history": [],
            "config": {"distill_threshold": 4000}
        }
        
        assert should_distill(state) == True
    
    def test_should_distill_returns_false_when_under_threshold(self):
        """should_distill returns False when context under threshold."""
        from src.agents.distiller import should_distill
        
        state = {
            "problem_state": "short",
            "research_context": "also short",
            "judge_context": None,
            "strategies": [],
            "history": [],
            "config": {"distill_threshold": 4000}
        }
        
        assert should_distill(state) == False


# ============================================================================
# End-to-End Test (Mock Mode)
# ============================================================================

@pytest.mark.asyncio
async def test_full_pipeline_mock_mode():
    """
    End-to-end test of the full pipeline in mock mode.
    
    This test verifies that all agents work together correctly
    without making actual API calls.
    """
    os.environ["USE_MOCK_AGENTS"] = "true"
    
    try:
        from src.core.graph_builder import build_deep_think_graph
        from src.core.state import DeepThinkState
        
        app = build_deep_think_graph()
        
        initial_state: DeepThinkState = {
            "problem_state": "如何设计一个高可用的微服务架构？",
            "strategies": [],
            "research_context": None,
            "research_status": None,
            "research_iteration": 0,
            "subtasks": None,
            "information_needs": None,
            "spatial_entropy": 1.0,  # High entropy to allow at least one iteration
            "effective_temperature": 1.0,
            "normalized_temperature": 0.5,
            "config": {
                "t_max": 2.0,
                "c_explore": 1.0,
                "beam_width": 3,
                "max_iterations": 1,  # Limit to 1 iteration for test speed
                "max_research_iterations": 1,
                "total_child_budget": 6
            },
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0,
            "judge_context": None,
            "architect_decisions": None
        }
        
        # Run the graph
        final_state = await app.ainvoke(initial_state)
        
        # Verify Phase 1 executed
        assert final_state.get("subtasks") is not None, "TaskDecomposer should create subtasks"
        assert final_state.get("research_context") is not None, "Researcher should gather context"
        
        # Verify strategies were generated
        assert len(final_state["strategies"]) >= 2, "Should have multiple strategies"
        
        # Verify each strategy went through the pipeline
        for s in final_state["strategies"]:
            assert s.get("name"), "Strategy should have a name"
            assert "score" in s, "Strategy should have been scored by Judge"
            assert s.get("status") == "active", "No hard pruning in pure Ising model"
        
        # Verify history has entries from all phases
        history = final_state.get("history", [])
        assert len(history) >= 3, "Should have history from multiple agents"
        
        print(f"\n[PASS] Full Pipeline Test Completed")
        print(f"  Strategies: {len(final_state['strategies'])}")
        print(f"  History entries: {len(history)}")
        print(f"  Iterations: {final_state.get('iteration_count', 0)}")
        
    finally:
        os.environ.pop("USE_MOCK_AGENTS", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
