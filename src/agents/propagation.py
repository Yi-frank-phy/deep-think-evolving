"""
Propagation Node - generates child strategies from active parents.

Implements the "繁殖 (Propagation)" step of the Evolutionary Beam Search (EBS).
Key features:
1. Configurable temperature coupling (auto/manual mode)
2. Uses child_quota from Boltzmann allocation (soft pruning)
3. One-Call-One-Strategy: each child is generated independently
4. Children inherit parent trajectory
"""

import os
import uuid
import json
from typing import List, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.state import DeepThinkState, StrategyNode


# Prompt template for generating child strategies
CHILD_GENERATION_PROMPT = """\
你是一位"战略进化师"，负责根据父策略生成一个变体子策略。

## 原始问题背景
{problem_state}

## 父策略
- 名称: {parent_name}
- 理由: {parent_rationale}
- 假设: {parent_assumption}

## 历史轨迹
{trajectory}

## 任务
基于父策略，生成一个**变体子策略**。你可以：
1. 改进父策略的某个薄弱环节
2. 探索父策略未涉及的另一种方向
3. 结合新的假设或约束

请确保子策略与父策略有所不同，但仍然针对原始问题。

## 输出格式 (严格 JSON)
{{
    "strategy_name": "子策略名称",
    "rationale": "子策略的理由和逻辑",
    "initial_assumption": "核心假设",
    "new_step": "本策略相比父策略的关键改进点（简短描述）"
}}
"""

# Default LLM temperature when in manual mode (DeepMind recommended)
DEFAULT_MANUAL_LLM_TEMP = 1.0


def calculate_llm_temperature(
    tau: float, 
    coupling_mode: str = "auto",
    manual_temp: Optional[float] = None
) -> float:
    """
    Calculate LLM temperature based on coupling mode.
    
    Args:
        tau: Normalized system temperature (T_eff / T_max)
        coupling_mode: "auto" (couple to tau) or "manual" (fixed temp)
        manual_temp: Temperature to use in manual mode (default: 1.0)
        
    Returns:
        LLM temperature in [0, 2] range (Gemini API range)
    """
    if coupling_mode == "manual":
        # Decoupled: use fixed temperature (DeepMind recommendation: 1.0)
        return manual_temp if manual_temp is not None else DEFAULT_MANUAL_LLM_TEMP
    
    # Auto mode: map tau to [0, 2] range
    # tau is T_eff / T_max, so if T_max = 2.0 (default), tau ∈ [0, ∞)
    # We clip to [0, 2] for LLM API
    llm_temp = min(2.0, max(0.0, tau))
    return llm_temp


def _generate_child_strategy(
    parent: StrategyNode,
    problem_state: str,
    llm_temperature: float,
    model_name: str,
    api_key: str,
) -> StrategyNode:
    """
    Generate a single child strategy from a parent.
    
    Implements "One-Call-One-Strategy" - each child comes from independent API call.
    """
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=llm_temperature,  # Dynamic or fixed based on coupling mode
    )
    
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=CHILD_GENERATION_PROMPT,
        input_variables=["problem_state", "parent_name", "parent_rationale", 
                        "parent_assumption", "trajectory"]
    )
    
    chain = prompt | llm | parser
    
    trajectory_str = "\n".join([f"- {step}" for step in parent.get("trajectory", [])])
    
    result = chain.invoke({
        "problem_state": problem_state,
        "parent_name": parent["name"],
        "parent_rationale": parent["rationale"],
        "parent_assumption": parent["assumption"],
        "trajectory": trajectory_str or "(无历史记录)"
    })
    
    # Build child node
    child: StrategyNode = {
        "id": str(uuid.uuid4()),
        "name": result.get("strategy_name", f"Child of {parent['name']}"),
        "rationale": result.get("rationale", ""),
        "assumption": result.get("initial_assumption", ""),
        "milestones": parent.get("milestones", []),  # Inherit milestones
        
        # Metrics to be computed in evolution
        "embedding": None,
        "density": None,
        "log_density": None,
        "score": 0.0,
        
        "status": "active",
        
        # Inherit parent trajectory + new step
        "trajectory": parent.get("trajectory", []).copy() + [
            f"[Propagation] {result.get('new_step', 'Generated as child variant')}"
        ],
        
        # Track lineage
        "parent_id": parent["id"],
    }
    
    return child


def _generate_mock_child(parent: StrategyNode, child_index: int = 0) -> StrategyNode:
    """Generate a mock child for testing without API calls."""
    import random
    
    suffixes = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
    suffix = suffixes[child_index % len(suffixes)]
    
    child: StrategyNode = {
        "id": str(uuid.uuid4()),
        "name": f"{parent['name']} - Variant {suffix}",
        "rationale": f"Extended from: {parent.get('rationale', '')[:50]}...",
        "assumption": f"Building on: {parent.get('assumption', '')[:50]}...",
        "milestones": parent.get("milestones", []),
        "embedding": None,
        "density": None,
        "log_density": None,
        "score": 0.0,
        "status": "active",
        "trajectory": parent.get("trajectory", []).copy() + [
            f"[Propagation Mock] Generated variant {suffix}"
        ],
        "parent_id": parent["id"],
    }
    
    return child


def propagation_node(state: DeepThinkState) -> DeepThinkState:
    """
    Propagation node: generate child strategies using Boltzmann allocation.
    
    Key changes from previous version:
    1. Uses child_quota from evolution (Boltzmann soft pruning) instead of fixed count
    2. Temperature coupling is configurable: "auto" or "manual"
    3. LLM temperature range extended to [0, 2] (full Gemini API range)
    
    Config options:
    - temperature_coupling: "auto" | "manual" (default: "auto")
    - manual_llm_temperature: float (default: 1.0, used when coupling="manual")
    """
    print("\n[Propagation] Generating child strategies...")
    
    # Get configuration
    config = state.get("config", {})
    coupling_mode = config.get("temperature_coupling", "auto")
    manual_temp = config.get("manual_llm_temperature", DEFAULT_MANUAL_LLM_TEMP)
    
    model_name = os.environ.get("GEMINI_MODEL_PROPAGATION", 
                                os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
    
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key
    
    # Calculate LLM temperature based on coupling mode
    tau = state.get("normalized_temperature", 0.5)
    llm_temperature = calculate_llm_temperature(tau, coupling_mode, manual_temp)
    
    print(f"  [Config] coupling={coupling_mode}, tau={tau:.3f}, llm_temp={llm_temperature:.3f}")
    
    strategies = state.get("strategies", [])
    
    # Get all strategies that have child_quota > 0 (from Boltzmann allocation)
    # If child_quota is not set (legacy mode), fall back to children_per_parent config
    parents_with_quota = [
        s for s in strategies 
        if s.get("status") == "active" and s.get("child_quota", 0) > 0
    ]
    
    # Fallback for legacy mode (no child_quota set)
    if not parents_with_quota:
        children_per_parent = config.get("children_per_parent", 2)
        parents_with_quota = [s for s in strategies if s.get("status") == "active"]
        for p in parents_with_quota:
            p["child_quota"] = children_per_parent
    
    if not parents_with_quota:
        print("  [Propagation] No parents with child quota to propagate from.")
        return state
    
    new_children: List[StrategyNode] = []
    total_quota = sum(p.get("child_quota", 0) for p in parents_with_quota)
    
    print(f"  [Allocation] {len(parents_with_quota)} parents, total quota: {total_quota}")
    
    for parent in parents_with_quota:
        quota = parent.get("child_quota", 0)
        if quota <= 0:
            continue
            
        print(f"  > Propagating from '{parent['name']}' (quota: {quota})...")
        
        for i in range(quota):
            try:
                if use_mock:
                    child = _generate_mock_child(parent, i)
                else:
                    child = _generate_child_strategy(
                        parent=parent,
                        problem_state=state["problem_state"],
                        llm_temperature=llm_temperature,
                        model_name=model_name,
                        api_key=api_key,
                    )
                new_children.append(child)
                print(f"    Created child {i+1}/{quota}: '{child['name']}'")
                
            except Exception as e:
                print(f"    [Error] Failed to generate child {i+1}: {e}")
    
    # Mark parents as 'expanded' (they exist in tree but aren't active for next round)
    for parent in parents_with_quota:
        parent["status"] = "expanded"
        children_created = len([c for c in new_children if c.get("parent_id") == parent["id"]])
        parent["trajectory"] = parent.get("trajectory", []) + [
            f"[Expanded] Generated {children_created} children (quota was {parent.get('child_quota', 0)})"
        ]
        # Clear quota after use
        parent["child_quota"] = 0
    
    # Add children to strategies list
    all_strategies = strategies + new_children
    
    print(f"[Propagation] Created {len(new_children)} new child strategies (coupling={coupling_mode}, llm_temp={llm_temperature:.2f})")
    
    return {
        **state,
        "strategies": all_strategies,
        "history": state.get("history", []) + [
            f"Propagation: {len(parents_with_quota)} parents -> {len(new_children)} children "
            f"(coupling={coupling_mode}, llm_temp={llm_temperature:.2f})"
        ]
    }

