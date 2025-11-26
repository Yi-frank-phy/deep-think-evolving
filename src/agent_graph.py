from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, TypedDict, Union

from langgraph.graph import END, StateGraph

from src.context_manager import (
    SummaryResult,
    append_step,
    create_context,
    generate_summary,
    record_reflection,
)
from src.diversity_calculator import calculate_similarity_matrix
from src.embedding_client import embed_strategies
from src.strategy_architect import generate_strategic_blueprint


class AgentState(TypedDict):
    """The state of the Deep Think agent."""

    problem_state: str
    strategies: List[Dict[str, Any]]
    embedded_strategies: List[Dict[str, Any]]
    similarity_matrix: Any  # numpy array
    summaries: Dict[str, SummaryResult]
    logs: Annotated[List[str], operator.add]
    thread_registry: List[Dict[str, Any]]


def blueprint_node(state: AgentState) -> Dict[str, Any]:
    """Generate strategic blueprint."""
    problem = state["problem_state"]
    strategies = generate_strategic_blueprint(problem)
    
    # Initialize contexts
    thread_registry = []
    for idx, strategy in enumerate(strategies, start=1):
        thread_id = f"strategy-{idx:02d}"
        context_path = create_context(thread_id)
        append_step(
            thread_id,
            {
                "event": "strategy_initialised",
                "strategy_name": strategy.get("strategy_name"),
                "rationale": strategy.get("rationale"),
                "initial_assumption": strategy.get("initial_assumption"),
                "milestones": strategy.get("milestones", {}),
            },
        )
        thread_registry.append(
            {
                "thread_id": thread_id,
                "context_path": context_path,
                "strategy": strategy,
            }
        )
    
    return {
        "strategies": strategies,
        "thread_registry": thread_registry,
        "logs": [f"Generated {len(strategies)} strategies."]
    }


def embedding_node(state: AgentState) -> Dict[str, Any]:
    """Embed strategies."""
    strategies = state["strategies"]
    embedded = embed_strategies(strategies)
    
    # Log embeddings to context
    thread_registry = state["thread_registry"]
    for idx, strategy in enumerate(embedded, start=1):
        if idx <= len(thread_registry):
            thread_id = thread_registry[idx - 1]["thread_id"]
            embedding = strategy.get("embedding") or []
            append_step(
                thread_id,
                {
                    "event": "embedding_generated",
                    "embedding_dimensions": len(embedding),
                    "embedding_preview": embedding[:8],
                },
            )

    return {
        "embedded_strategies": embedded,
        "logs": ["Strategies embedded successfully."]
    }


def similarity_node(state: AgentState) -> Dict[str, Any]:
    """Calculate similarity matrix."""
    embedded = state["embedded_strategies"]
    matrix = calculate_similarity_matrix(embedded)
    
    # Log scores to context
    thread_registry = state["thread_registry"]
    for idx, registry_entry in enumerate(thread_registry):
        if idx < len(matrix):
            append_step(
                registry_entry["thread_id"],
                {
                    "event": "similarity_scores",
                    "scores": matrix[idx].tolist(),
                },
            )

    return {
        "similarity_matrix": matrix,
        "logs": ["Similarity matrix calculated."]
    }


def summary_node(state: AgentState) -> Dict[str, Any]:
    """Generate summaries for each thread."""
    thread_registry = state["thread_registry"]
    summaries = {}
    
    for registry_entry in thread_registry:
        thread_id = registry_entry["thread_id"]
        summary_result = generate_summary(thread_id)
        registry_entry["summary"] = summary_result
        summaries[thread_id] = summary_result
    
    return {
        "summaries": summaries,
        "logs": [f"Generated summaries for {len(summaries)} threads."]
    }


def build_graph():
    """Build the LangGraph state machine."""
    workflow = StateGraph(AgentState)

    workflow.add_node("blueprint", blueprint_node)
    workflow.add_node("embedding", embedding_node)
    workflow.add_node("similarity", similarity_node)
    workflow.add_node("summary", summary_node)

    workflow.set_entry_point("blueprint")

    workflow.add_edge("blueprint", "embedding")
    workflow.add_edge("embedding", "similarity")
    workflow.add_edge("similarity", "summary")
    workflow.add_edge("summary", END)

    return workflow.compile()
