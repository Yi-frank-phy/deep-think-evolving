
from __future__ import annotations
from typing import List, Dict, Any, Optional, TypedDict, Union
from typing_extensions import Annotated
import operator

# Use Annotated with operator.add for reducers if needed, 
# but for now we might replace lists entirely or append.
# For strategies, we usually want to replace the list or update it.

class StrategyNode(TypedDict):
    """
    Represents a single strategy (node) in the evolutionary beam.
    """
    id: str
    name: str # strategy_name
    rationale: str
    assumption: str # initial_assumption
    milestones: Any # JSON object
    
    # Evolution Metrics
    embedding: Optional[List[float]]
    density: Optional[float]
    log_density: Optional[float]
    score: Optional[float] # UCB Score
    
    # Status
    status: str # 'active', 'pruned', 'completed', 'expanded'
    
    # Execution
    trajectory: List[str] # Detailed execution steps/observations
    
    # Parent tracking for tree visualization
    parent_id: Optional[str]

class DeepThinkState(TypedDict):
    """
    Global state for the Deep Think optimization process.
    """
    # Input
    problem_state: str
    
    # Evolution State
    strategies: List[StrategyNode]
    
    # Research Context
    research_context: Optional[str]
    
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
    
    # Distilled context for Judge (prevents context rot)
    judge_context: Optional[str]


