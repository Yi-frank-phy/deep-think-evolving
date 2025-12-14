"""
Tests for Hard Pruning Mechanism and Strategy Archiving

Based on spec.md §13 (硬剪枝机制):
- Report = Pruning Signal
- Active strategies are hard pruned after synthesis
- Value preserved in: report + knowledge base vector DB
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import json
from pathlib import Path


class TestStrategyArchive:
    """Test knowledge base archiving for pruned strategies."""
    
    def test_write_strategy_archive_import(self):
        """Test that write_strategy_archive can be imported."""
        from src.tools.knowledge_base import write_strategy_archive
        assert callable(write_strategy_archive)
    
    def test_write_strategy_archive_creates_file(self, tmp_path):
        """Test that archiving creates a JSON file with correct structure."""
        from src.tools.knowledge_base import write_strategy_archive
        
        # Set temp knowledge base path
        with patch.dict(os.environ, {"KNOWLEDGE_BASE_PATH": str(tmp_path)}):
            strategy = {
                "id": "test-strategy-id",
                "name": "测试策略",
                "rationale": "测试理由",
                "assumption": "测试假设",
                "score": 0.85,
                "status": "active",
                "trajectory": ["[Executor] Task 1", "[Judge] Score: 8.5"]
            }
            
            result = write_strategy_archive(
                strategy=strategy,
                synthesis_context="在报告 v1 中被综合",
                branch_rationale="选择此分支因为分数最高",
                report_version=1
            )
            
            # Check file was created
            assert "archived" in result.lower() or "saved" in result.lower()
            
            # Find the created file
            files = list(tmp_path.glob("*.json"))
            assert len(files) == 1
            
            # Check file content
            with open(files[0], encoding="utf-8") as f:
                archive = json.load(f)
            
            assert archive["type"] == "strategy_archive"
            assert "测试策略" in archive["title"]
            assert "report_v1" in archive["tags"]
    
    def test_archive_contains_required_fields(self, tmp_path):
        """Test that archived strategy contains all required fields per spec."""
        from src.tools.knowledge_base import write_strategy_archive
        
        with patch.dict(os.environ, {"KNOWLEDGE_BASE_PATH": str(tmp_path)}):
            strategy = {
                "id": "spec-test-id",
                "name": "规范测试策略",
                "rationale": "详细理由说明",
                "assumption": "核心假设",
                "score": 0.75,
                "status": "active",
                "trajectory": ["step1", "step2", "step3"]
            }
            
            write_strategy_archive(
                strategy=strategy,
                synthesis_context="测试综合上下文",
                branch_rationale="测试分支决策",
                report_version=2
            )
            
            files = list(tmp_path.glob("*.json"))
            with open(files[0], encoding="utf-8") as f:
                archive = json.load(f)
            
            # Per spec.md §6.3, must contain:
            content = json.loads(archive["content"])
            assert "strategy_name" in content
            assert "rationale" in content
            assert "assumption" in content
            assert "trajectory_summary" in content
            assert "branch_rationale" in content
            assert "synthesis_context" in content
            assert "report_version" in content


class TestHardPruning:
    """Test hard pruning mechanism in executor."""
    
    def test_synthesis_returns_prune_ids(self):
        """Test that synthesis task returns strategy IDs to prune."""
        from src.agents.executor import execute_synthesis_task
        
        strategies = [
            {"id": "s1", "name": "策略1", "status": "active", "score": 0.8, "rationale": "r1", "assumption": "a1", "trajectory": []},
            {"id": "s2", "name": "策略2", "status": "active", "score": 0.7, "rationale": "r2", "assumption": "a2", "trajectory": []},
            {"id": "s3", "name": "策略3", "status": "pruned", "score": 0.5, "rationale": "r3", "assumption": "a3", "trajectory": []},
        ]
        
        result = execute_synthesis_task(
            problem="测试问题",
            strategies=strategies,
            decision={"executor_instruction": "综合所有发现"},
            research_context=None,
            existing_report=None,
            report_version=0,
            api_key="",
            use_mock=True
        )
        
        # Should return IDs of ACTIVE strategies only
        assert "prune_strategy_ids" in result
        assert "s1" in result["prune_strategy_ids"]
        assert "s2" in result["prune_strategy_ids"]
        assert "s3" not in result["prune_strategy_ids"]  # Already pruned
    
    def test_synthesis_returns_branch_rationale(self):
        """Test that synthesis task returns branch rationale for KB archiving."""
        from src.agents.executor import execute_synthesis_task
        
        result = execute_synthesis_task(
            problem="测试",
            strategies=[{"id": "x", "name": "X", "status": "active", "score": 0.5, "rationale": "", "assumption": "", "trajectory": []}],
            decision={"executor_instruction": "综合"},
            research_context=None,
            existing_report=None,
            report_version=0,
            api_key="",
            use_mock=True
        )
        
        assert "branch_rationale" in result
        assert result["branch_rationale"]  # Not empty


class TestPrunedSynthesizedStatus:
    """Test that pruned_synthesized status is properly defined."""
    
    def test_state_allows_pruned_synthesized(self):
        """Test that DeepThinkState StrategyNode accepts pruned_synthesized status."""
        from src.core.state import StrategyNode
        
        # Create a strategy with pruned_synthesized status
        strategy: StrategyNode = {
            "id": "test",
            "name": "test",
            "rationale": "test",
            "assumption": "test",
            "milestones": [],
            "embedding": None,
            "density": None,
            "log_density": None,
            "score": 0.5,
            "status": "pruned_synthesized",  # New status
            "trajectory": [],
            "parent_id": None
        }
        
        assert strategy["status"] == "pruned_synthesized"


class TestArchitectPruningWarning:
    """Test that Architect prompt includes pruning warning."""
    
    def test_prompt_has_pruning_warning(self):
        """Test that Architect prompt warns about hard pruning."""
        from src.agents.architect import ARCHITECT_SCHEDULER_PROMPT
        
        assert "硬剪枝" in ARCHITECT_SCHEDULER_PROMPT or "hard prune" in ARCHITECT_SCHEDULER_PROMPT.lower()
        assert "不可逆" in ARCHITECT_SCHEDULER_PROMPT or "irreversible" in ARCHITECT_SCHEDULER_PROMPT.lower()


class TestExecutorSynthesisPrompt:
    """Test that Executor synthesis prompt informs about pruning."""
    
    def test_prompt_informs_pruning(self):
        """Test that synthesis prompt tells LLM about pruning."""
        from src.agents.executor import SYNTHESIS_PROMPT_TEMPLATE
        
        assert "硬剪枝" in SYNTHESIS_PROMPT_TEMPLATE or "剪枝" in SYNTHESIS_PROMPT_TEMPLATE
        assert "完整保留" in SYNTHESIS_PROMPT_TEMPLATE or "保留" in SYNTHESIS_PROMPT_TEMPLATE
