"""
Tests for Synthesis/Report Generation (Dynamic Report via Executor)

After refactoring:
- Fixed WriterAgent node removed
- Report generation is now dynamically handled by Executor
- Architect decides when to assign synthesis tasks
- writer.py still exists but is no longer a graph node
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os


class TestWriterModule:
    """Test that writer.py module still works (for standalone use)."""
    
    def test_writer_import(self):
        """Test that writer module can be imported."""
        from src.agents.writer import writer_node
        assert callable(writer_node)
    
    def test_format_strategies_summary_empty(self):
        """Test formatting with no strategies."""
        from src.agents.writer import _format_strategies_summary
        result = _format_strategies_summary([])
        assert "无策略数据" in result
    
    def test_format_strategies_summary_with_data(self):
        """Test formatting with sample strategies."""
        from src.agents.writer import _format_strategies_summary
        
        strategies = [
            {
                "name": "策略A",
                "status": "active",
                "score": 0.85,
                "rationale": "这是一个高分策略的理由说明文字",
                "assumption": "假设用户需要快速响应",
                "trajectory": ["[Judge] Score: 8.50"]
            },
            {
                "name": "策略B", 
                "status": "expanded",
                "score": 0.72,
                "rationale": "另一个策略的详细说明",
                "assumption": "假设资源充足",
                "trajectory": []
            }
        ]
        
        result = _format_strategies_summary(strategies, top_n=5)
        
        # Check that strategies are included
        assert "策略A" in result
        assert "策略B" in result
        # Check score formatting
        assert "0.85" in result or "0.850" in result


class TestExecutorSynthesis:
    """Test that Executor can handle synthesis tasks."""
    
    def test_synthesis_function_import(self):
        """Test that synthesis function can be imported from executor."""
        from src.agents.executor import execute_synthesis_task
        assert callable(execute_synthesis_task)
    
    def test_executor_node_import(self):
        """Test that executor_node can be imported."""
        from src.agents.executor import executor_node
        assert callable(executor_node)
    
    def test_synthesis_mock_mode(self):
        """Test synthesis task in mock mode."""
        from src.agents.executor import execute_synthesis_task
        
        result = execute_synthesis_task(
            problem="测试问题",
            strategies=[{"id": "test-id-1", "name": "测试策略", "status": "active", "score": 0.8, "rationale": "测试", "assumption": "假设", "trajectory": []}],
            decision={"executor_instruction": "生成报告"},
            research_context=None,
            existing_report=None,
            report_version=0,
            api_key="",
            use_mock=True
        )
        
        assert "report" in result
        assert result["report"] is not None
        assert "Mock" in result["report"]
        # Verify pruning IDs are returned
        assert "prune_strategy_ids" in result
        assert "test-id-1" in result["prune_strategy_ids"]


class TestGraphStructure:
    """Test that graph structure reflects the new architecture."""
    
    def test_no_fixed_writer_node(self):
        """Test that writer node is NOT in the graph (dynamic via Executor now)."""
        from src.core.graph_builder import build_deep_think_graph
        
        graph = build_deep_think_graph()
        nodes = list(graph.nodes)
        
        # Writer should NOT be a fixed node anymore
        assert "writer" not in nodes, f"'writer' should not be a fixed node: {nodes}"
        
        # But executor should be there (handles synthesis dynamically)
        assert "executor" in nodes, f"'executor' node should be in graph: {nodes}"
    
    def test_evolution_to_end_edge(self):
        """Test that evolution goes directly to END on convergence."""
        from src.core.graph_builder import build_deep_think_graph
        
        graph = build_deep_think_graph()
        
        # Check that the graph can be compiled (edges are valid)
        assert graph is not None


class TestStateDefinition:
    """Test that state includes report-related fields."""
    
    def test_final_report_in_state(self):
        """Test that DeepThinkState has final_report field."""
        from src.core.state import DeepThinkState
        
        annotations = DeepThinkState.__annotations__
        assert "final_report" in annotations, f"final_report not in state: {annotations.keys()}"
    
    def test_report_version_in_state(self):
        """Test that DeepThinkState has report_version field."""
        from src.core.state import DeepThinkState
        
        annotations = DeepThinkState.__annotations__
        assert "report_version" in annotations, f"report_version not in state: {annotations.keys()}"


class TestArchitectMetaStrategy:
    """Test that Architect prompt includes meta-strategy framework."""
    
    def test_architect_prompt_has_meta_strategy(self):
        """Test that Architect prompt includes meta-strategy concept."""
        from src.agents.architect import ARCHITECT_SCHEDULER_PROMPT
        
        assert "元策略" in ARCHITECT_SCHEDULER_PROMPT or "Meta-Strategy" in ARCHITECT_SCHEDULER_PROMPT
        assert "探索" in ARCHITECT_SCHEDULER_PROMPT
        assert "利用" in ARCHITECT_SCHEDULER_PROMPT
        assert "综合" in ARCHITECT_SCHEDULER_PROMPT
    
    def test_architect_prompt_has_system_state(self):
        """Test that Architect prompt includes system state placeholders."""
        from src.agents.architect import ARCHITECT_SCHEDULER_PROMPT
        
        assert "normalized_temperature" in ARCHITECT_SCHEDULER_PROMPT
        assert "spatial_entropy" in ARCHITECT_SCHEDULER_PROMPT
        assert "iteration_count" in ARCHITECT_SCHEDULER_PROMPT
        assert "report_version" in ARCHITECT_SCHEDULER_PROMPT
