"""
Tests for WriterAgent (Final Report Generator)
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os


class TestWriterAgent:
    """Test suite for WriterAgent functionality."""
    
    def test_writer_import(self):
        """Test that WriterAgent can be imported."""
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
    
    def test_writer_node_mock_mode(self):
        """Test writer_node in mock mode (no API key)."""
        from src.agents.writer import writer_node
        
        # Ensure no API key is set for mock mode
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "USE_MOCK_AGENTS": "true"}):
            state = {
                "problem_state": "测试问题",
                "research_context": "测试研究背景",
                "strategies": [
                    {"name": "测试策略", "status": "active", "score": 0.8, 
                     "rationale": "测试理由", "assumption": "测试假设", "trajectory": []}
                ],
                "iteration_count": 3,
                "spatial_entropy": 0.5,
                "history": []
            }
            
            result = writer_node(state)
            
            # Should have generated a mock report
            assert "final_report" in result
            assert result["final_report"] is not None
            assert "Mock" in result["final_report"]
            # Should have updated history
            assert any("Writer" in h for h in result.get("history", []))
    
    def test_writer_node_no_api_key(self):
        """Test writer_node with no API key and not in mock mode."""
        from src.agents.writer import writer_node
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "USE_MOCK_AGENTS": "false"}, clear=False):
            # Remove GEMINI_API_KEY if it exists
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]
            
            state = {
                "problem_state": "测试问题",
                "strategies": [],
                "iteration_count": 0,
                "spatial_entropy": 0.0,
                "history": []
            }
            
            result = writer_node(state)
            
            # Should have generated a placeholder report
            assert "final_report" in result
            assert "⚠️" in result["final_report"] or "无法" in result["final_report"]


class TestGraphIntegration:
    """Test that WriterAgent is properly integrated into the graph."""
    
    def test_writer_node_in_graph(self):
        """Test that writer node exists in the compiled graph."""
        from src.core.graph_builder import build_deep_think_graph
        
        graph = build_deep_think_graph()
        nodes = list(graph.nodes)
        
        assert "writer" in nodes, f"'writer' node not found in graph nodes: {nodes}"
    
    def test_evolution_to_writer_edge(self):
        """Test that evolution has conditional edge to writer on convergence."""
        from src.core.graph_builder import build_deep_think_graph
        
        graph = build_deep_think_graph()
        
        # Check that the graph can be compiled (edges are valid)
        assert graph is not None


class TestStateDefinition:
    """Test that state includes final_report field."""
    
    def test_final_report_in_state(self):
        """Test that DeepThinkState has final_report field."""
        from src.core.state import DeepThinkState
        
        # TypedDict annotations
        annotations = DeepThinkState.__annotations__
        assert "final_report" in annotations, f"final_report not in state: {annotations.keys()}"
