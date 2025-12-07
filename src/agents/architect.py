
import os
import uuid
from typing import List

from src.core.state import DeepThinkState, StrategyNode
from src.strategy_architect import generate_strategic_blueprint
from src.tools.knowledge_base import (
    get_all_experiences_for_embedding,
    format_experiences_for_context
)


def _retrieve_relevant_experiences(problem: str, limit: int = 3) -> str:
    """
    Retrieve experiences from knowledge base relevant to the problem.
    
    Currently uses simple text matching. TODO: Replace with vector search.
    """
    experiences = get_all_experiences_for_embedding()
    
    if not experiences:
        return ""
    
    # Simple relevance scoring (word overlap)
    problem_words = set(problem.lower().split())
    
    scored = []
    for exp in experiences:
        title_words = set(exp.get("title", "").lower().split())
        content_words = set(exp.get("content", "").lower().split())
        tags = set(tag.lower() for tag in exp.get("tags", []))
        
        # Score by word overlap
        overlap = len(problem_words & (title_words | content_words | tags))
        if overlap > 0:
            scored.append((overlap, exp))
    
    # Sort by relevance and take top
    scored.sort(key=lambda x: x[0], reverse=True)
    relevant = [exp for _, exp in scored[:limit]]
    
    return format_experiences_for_context(relevant)


def strategy_architect_node(state: DeepThinkState) -> DeepThinkState:
    """
    Node function to generate initial strategic blueprints.
    
    Enhanced with knowledge base retrieval:
    - Searches for relevant past experiences before generation
    - Injects experience context into the generation prompt
    """
    problem = state["problem_state"]
    print(f"\n[Architect] Generating strategies for: {problem[:50]}...")
    
    # Retrieve relevant experiences from knowledge base
    experience_context = _retrieve_relevant_experiences(problem)
    if experience_context:
        print(f"[Architect] Found relevant experiences in knowledge base")
        # Prepend experience context to problem
        enhanced_problem = f"{experience_context}\n\n## 当前问题\n{problem}"
    else:
        enhanced_problem = problem
    
    # Check for Mock Mode or Missing Key
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key

    if use_mock:
        print("[Architect] Running in MOCK MODE (Key missing or forced).")
        raw_strategies = [
            {"strategy_name": "Mock Strategy A (Solar)", "rationale": "Solar capture is efficient.", "initial_assumption": "Materials available.", "milestones": ["Build", "Launch"]},
            {"strategy_name": "Mock Strategy B (Nuclear)", "rationale": "Nuclear is dense.", "initial_assumption": "Fusion solved.", "milestones": ["Ignite", "Sustain"]},
            {"strategy_name": "Mock Strategy C (Swarm)", "rationale": "Swarm is resilient.", "initial_assumption": "AI control solved.", "milestones": ["Replicate", "Coordination"]}
        ]
    else:
        # Call the legacy function with enhanced problem context
        thinking_budget = state.get("config", {}).get("thinking_budget", 1024)
        raw_strategies = generate_strategic_blueprint(enhanced_problem, thinking_budget=thinking_budget)
    
    new_strategy_nodes: List[StrategyNode] = []
    
    for raw in raw_strategies:
        node: StrategyNode = {
            "id": str(uuid.uuid4()),
            "name": raw["strategy_name"],
            "rationale": raw["rationale"],
            "assumption": raw["initial_assumption"],
            "milestones": raw.get("milestones", []),
            
            # Initialize metrics
            "embedding": None,
            "density": None,
            "log_density": None,
            "score": 0.0,
            
            "status": "active",
            "trajectory": ["[Architect] Initial generation"]
        }
        new_strategy_nodes.append(node)
        
    print(f"[Architect] Generated {len(new_strategy_nodes)} strategies.")
    
    kb_used = "with KB context" if experience_context else "no KB context"
    
    return {
        **state,
        "strategies": new_strategy_nodes,
        "history": state.get("history", []) + [
            f"Architect generated {len(new_strategy_nodes)} strategies ({kb_used})"
        ]
    }

