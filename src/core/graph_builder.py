"""
Graph Builder - Deep Think Evolving 主流程图

重构后的流程：
Phase 1 (问题理解): TaskDecomposer → Researcher → StrategyGenerator
Phase 2 (初评): Judge → Evolution  
Phase 3 (执行循环): ArchitectScheduler → Executor → Judge → Evolution → (收敛?)
横切关注点: Distiller 在需要时动态触发
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from src.core.state import DeepThinkState

# New Agent imports
from src.agents.task_decomposer import task_decomposer_node
from src.agents.researcher import research_node
from src.agents.strategy_generator import strategy_generator_node
from src.agents.architect import architect_scheduler_node, strategy_architect_node
from src.agents.propagation import propagation_node  # 子节点生成

# Existing agents
from src.agents.judge import judge_node
from src.agents.evolution import evolution_node
from src.agents.executor import executor_node
from src.agents.distiller import distiller_node, distiller_for_judge_node
# Note: writer_node removed - report generation is now dynamically handled by Executor
# Note: distiller_node now runs BEFORE strategy_generator for context purity


def should_continue(state: DeepThinkState) -> Literal["continue", "end"]:
    """
    Determines whether the evolution loop should continue or end.
    
    Convergence conditions (any triggers 'end'):
    1. iteration_count >= max_iterations (default: 10)
    2. Entropy has stabilized (relative change below threshold)
    3. No active strategies remain
    
    Note: In high-dimensional spaces, differential entropy can be negative.
    We use entropy CHANGE RATE (not absolute value) for convergence detection.
    First iteration automatically continues since no previous entropy exists.
    
    Returns:
        "continue" to keep evolving, "end" to terminate.
    """
    config = state.get("config", {})
    max_iterations = config.get("max_iterations", 10)
    entropy_change_threshold = config.get("entropy_change_threshold", 0.1)  # Relative change
    
    iteration_count = state.get("iteration_count", 0)
    spatial_entropy = state.get("spatial_entropy", 0.0)
    prev_entropy = state.get("prev_spatial_entropy", None)
    strategies = state.get("strategies", [])
    
    # Check if iteration limit reached
    if iteration_count >= max_iterations:
        print(f"[Convergence] Max iterations ({max_iterations}) reached. Ending.")
        return "end"
    
    # Check if any active strategies remain
    active_strategies = [s for s in strategies if s.get("status") == "active"]
    if not active_strategies:
        print("[Convergence] No active strategies remain. Ending.")
        return "end"
    
    # Entropy convergence check (natural: skipped on first iteration when prev_entropy is None)
    if prev_entropy is not None:
        # Use relative change for convergence (handles both positive and negative entropy)
        entropy_change = abs(spatial_entropy - prev_entropy)
        reference = max(abs(spatial_entropy), abs(prev_entropy), 1.0)  # Avoid division by zero
        relative_change = entropy_change / reference
        
        if relative_change < entropy_change_threshold:
            print(f"[Convergence] Entropy stabilized (change={relative_change:.4f} < {entropy_change_threshold}). Converged!")
            return "end"
        else:
            print(f"[Convergence] Continuing (iter={iteration_count}, entropy={spatial_entropy:.4f}, change={relative_change:.4f})")
    else:
        # First iteration - no previous entropy to compare
        print(f"[Convergence] Continuing (iter={iteration_count}, entropy={spatial_entropy:.4f}, first iteration)")
    
    return "continue"


def should_research_continue(state: DeepThinkState) -> Literal["research_more", "proceed"]:
    """
    Determines whether Researcher should continue gathering information.
    
    Based on research_status from Researcher's self-reflection.
    Limited by max_research_iterations config.
    """
    config = state.get("config", {})
    max_iterations = config.get("max_research_iterations", 3)
    current_iteration = state.get("research_iteration", 0)
    research_status = state.get("research_status", "sufficient")
    
    if current_iteration >= max_iterations:
        print(f"[Research] Max research iterations ({max_iterations}) reached. Proceeding.")
        return "proceed"
    
    if research_status == "insufficient":
        print(f"[Research] Information insufficient. Continuing research.")
        return "research_more"
    
    print(f"[Research] Information sufficient. Proceeding to strategy generation.")
    return "proceed"


def build_deep_think_graph():
    """
    Constructs the Deep Think Evolving StateGraph with new Agent architecture.
    
    New Flow:
    Phase 1 - Problem Understanding:
        TaskDecomposer -> Researcher -> (sufficient?) -> StrategyGenerator
        
    Phase 2 - Initial Evaluation:
        DistillerForJudge -> Judge -> Evolution
        
    Phase 3 - Execution Loop:
        Evolution -> (should_continue?) 
            -> ArchitectScheduler -> Executor -> DistillerForJudge -> Judge -> Evolution
            -> WriterAgent -> END (if converged)
    
    Key Features:
    - TaskDecomposer breaks down problem into subtasks and information needs
    - Researcher uses single-call self-reflection (cost optimized, not ReAct)
    - StrategyGenerator creates initial strategies (separated from Architect)
    - Architect now schedules execution tasks (UCB-driven)
    - Executor executes tasks and can generate variants
    - distiller_for_judge runs BEFORE every Judge call for clean context
    """
    workflow = StateGraph(DeepThinkState)
    
    # ========== Phase 1: Problem Understanding ==========
    workflow.add_node("task_decomposer", task_decomposer_node)
    workflow.add_node("researcher", research_node)
    workflow.add_node("distiller", distiller_node)  # Required: context purity for StrategyGenerator
    workflow.add_node("strategy_generator", strategy_generator_node)
    
    # ========== Phase 2 & 3: Evaluation & Execution ==========
    workflow.add_node("distiller_for_judge", distiller_for_judge_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("evolution", evolution_node)
    workflow.add_node("propagation", propagation_node)  # 新增: 子节点生成
    workflow.add_node("architect_scheduler", architect_scheduler_node)
    workflow.add_node("executor", executor_node)
    # Note: Report generation is now dynamically handled by Executor (no fixed writer node)
    
    # ========== Entry Point ==========
    workflow.set_entry_point("task_decomposer")
    
    # ========== Phase 1 Edges ==========
    # TaskDecomposer -> Researcher
    workflow.add_edge("task_decomposer", "researcher")
    
    # Researcher -> (check if info sufficient) -> Distiller -> StrategyGenerator or loop
    workflow.add_conditional_edges(
        "researcher",
        should_research_continue,
        {
            "research_more": "researcher",  # Loop back for more research
            "proceed": "distiller"  # Distill before strategy generation
        }
    )
    
    # Distiller -> StrategyGenerator (forced distillation for context purity)
    workflow.add_edge("distiller", "strategy_generator")
    
    # StrategyGenerator -> DistillerForJudge (initial evaluation)
    workflow.add_edge("strategy_generator", "distiller_for_judge")
    
    # ========== Phase 2: Initial Evaluation ==========
    workflow.add_edge("distiller_for_judge", "judge")
    workflow.add_edge("judge", "evolution")
    
    # ========== Phase 3: Execution Loop ==========
    # Evolution → (should_continue?) → Propagation → ArchitectScheduler or END
    # should_continue checks BEFORE propagation (if child_quota exists, we continue)
    workflow.add_conditional_edges(
        "evolution",
        should_continue,
        {
            "continue": "propagation",  # Create child nodes
            "end": END  # Report already generated by Executor if Architect assigned synthesis
        }
    )
    
    # Propagation -> ArchitectScheduler (child nodes created, now schedule execution)
    workflow.add_edge("propagation", "architect_scheduler")
    
    # ArchitectScheduler -> Executor -> DistillerForJudge -> Judge -> Evolution (loop)
    workflow.add_edge("architect_scheduler", "executor")
    workflow.add_edge("executor", "distiller_for_judge")
    # Note: distiller_for_judge -> judge -> evolution edges already defined above
    
    # ========== Compile ==========
    # Set recursion_limit to allow for research loops and evolution loops
    # Default is 25, we need more for complex problems
    app = workflow.compile()
    app.recursion_limit = 50  # Allow up to 50 recursive calls
    return app
