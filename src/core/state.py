
from __future__ import annotations
from typing import List, Dict, Any, Optional, TypedDict, Union, Literal
from typing_extensions import Annotated
import operator

# Use Annotated with operator.add for reducers if needed, 
# but for now we might replace lists entirely or append.
# For strategies, we usually want to replace the list or update it.

# Strategy status values as defined in spec.md §3.3
StrategyStatus = Literal["active", "pruned", "completed", "expanded", "pruned_synthesized"]

class StrategyNode(TypedDict):
    """
    Represents a single strategy (node) in the evolutionary beam.
    Spec Reference: spec.md §3.3
    """
    id: str
    name: str  # strategy_name
    rationale: str
    assumption: str  # initial_assumption
    milestones: Any  # JSON object
    
    # Evolution Metrics (spec.md §3.3)
    embedding: Optional[List[float]]  # 嵌入向量 (4096维 for Qwen3-Embedding-8B)
    density: Optional[float]  # KDE 密度
    log_density: Optional[float]  # 对数密度
    score: Optional[float]  # Judge评分 (0-1)
    ucb_score: Optional[float]  # UCB综合评分 (用于排序/展示)
    child_quota: Optional[int]  # Boltzmann分配的子节点配额
    
    # Status (spec.md §3.3)
    status: StrategyStatus
    
    # Execution
    trajectory: List[str]  # Detailed execution steps/observations
    
    # Parent tracking for tree visualization
    parent_id: Optional[str]
    
    # Hard pruning tracking (spec.md §13)
    pruned_at_report_version: Optional[int]  # 被剪枝时的报告版本
    
    # Full response for UI expansion (T-050)
    full_response: Optional[str]  # 完整 AI 回答
    thinking_summary: Optional[str]  # Gemini 思维链摘要


class DeepThinkState(TypedDict):
    """
    Global state for the Deep Think optimization process.
    """
    # Input
    problem_state: str
    
    # Task Decomposition (from TaskDecomposer)
    subtasks: Optional[List[str]]
    information_needs: Optional[List[Dict[str, Any]]]  # [{topic, type, priority}]
    
    # Evolution State
    strategies: List[StrategyNode]
    
    # Research Context
    research_context: Optional[str]
    research_status: Optional[str]  # "sufficient" | "insufficient"
    
    # Global Metrics
    spatial_entropy: float
    effective_temperature: float
    normalized_temperature: float
    
    # Configuration (Hyperparameters)
    config: Dict[str, Any]
    
    # Memory / Virtual File System
    # Placeholder for now, can be a simple Dict
    virtual_filesystem: Dict[str, str]
    
    # History of operations for transparency
    history: Annotated[List[str], operator.add]
    
    # Iteration tracking for convergence
    iteration_count: int
    
    # Research iteration tracking
    research_iteration: Optional[int]
    
    # Distilled context for Judge (prevents context rot)
    judge_context: Optional[str]
    
    # Architect decisions for Executor
    architect_decisions: Optional[List[Dict[str, Any]]]  # [{strategy_id, executor_instruction, context_injection}]
    
    # Final Report (generated dynamically by Executor when Architect assigns synthesis tasks)
    final_report: Optional[str]
    report_version: Optional[int]  # Report version number, supports incremental updates

