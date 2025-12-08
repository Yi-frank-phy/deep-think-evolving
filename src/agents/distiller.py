"""
Distiller Agent - 信息蒸馏器

负责压缩上下文，防止 Context Rot（上下文腐烂）。
支持动态触发：当上下文超过阈值时自动调用。
"""

import os
from typing import List, Optional, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.state import DeepThinkState, StrategyNode


def estimate_token_count(state: DeepThinkState) -> int:
    """
    Estimate the token count of current state context.
    
    Uses a rough estimate of 4 characters per token for Chinese/mixed content.
    """
    total_chars = 0
    
    # Problem state
    total_chars += len(state.get("problem_state", ""))
    
    # Research context
    total_chars += len(state.get("research_context", "") or "")
    
    # Judge context
    total_chars += len(state.get("judge_context", "") or "")
    
    # Strategies (trajectories can get long)
    for s in state.get("strategies", []):
        total_chars += len(s.get("rationale", ""))
        total_chars += len(s.get("assumption", ""))
        for t in s.get("trajectory", []):
            total_chars += len(t)
    
    # History
    for h in state.get("history", []):
        total_chars += len(h)
    
    # Rough estimate: 4 chars per token for mixed Chinese/English
    return total_chars // 4


def should_distill(state: DeepThinkState) -> bool:
    """
    Dynamic trigger: determine if Distiller should run.
    
    Returns True if context exceeds the configured threshold.
    """
    config = state.get("config", {})
    threshold = config.get("distill_threshold", 4000)  # tokens
    
    current_tokens = estimate_token_count(state)
    
    return current_tokens > threshold


def conditional_distill(state: DeepThinkState) -> DeepThinkState:
    """
    Conditionally run distillation if context exceeds threshold.
    
    This can be called before any Agent to prevent context rot.
    """
    if should_distill(state):
        print(f"[Distiller] Context exceeds threshold, triggering distillation...")
        return distiller_for_judge_node(state)  # Use the lighter distiller
    return state


def _get_llm():
    """Get the Distiller LLM instance."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    
    model_name = os.environ.get("GEMINI_MODEL_DISTILLER", 
                                os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.2,
    )


def _summarize_strategies(strategies: List[StrategyNode]) -> str:
    """Create a concise summary of all strategies and their status."""
    if not strategies:
        return "无策略"
    
    active = [s for s in strategies if s.get("status") == "active"]
    pruned = [s for s in strategies if s.get("status") in ("pruned", "pruned_beam")]
    expanded = [s for s in strategies if s.get("status") == "expanded"]
    
    lines = []
    
    if active:
        lines.append(f"🟢 活跃策略 ({len(active)}):")
        for s in active[:5]:  # Top 5
            score = s.get("score", 0)
            lines.append(f"  - {s['name']} (score: {score:.2f})")
    
    if pruned:
        lines.append(f"🔴 被剪枝策略 ({len(pruned)}):")
        for s in pruned[:3]:  # Top 3
            # Extract last trajectory entry for reason
            traj = s.get("trajectory", [])
            reason = traj[-1] if traj else "未知原因"
            lines.append(f"  - {s['name']}: {reason[:80]}")
    
    if expanded:
        lines.append(f"🔵 已扩展策略 ({len(expanded)}):")
        for s in expanded[:3]:
            lines.append(f"  - {s['name']}")
    
    return "\n".join(lines)


def _summarize_history(history: List[str], limit: int = 5) -> str:
    """Summarize recent history events."""
    if not history:
        return "无历史记录"
    
    recent = history[-limit:]
    return "\n".join([f"• {event}" for event in recent])


def distiller_node(state: DeepThinkState) -> DeepThinkState:
    """
    Distills the raw research context into a concise, actionable summary
    and injects it into the problem state.
    
    This runs ONCE at the start of the pipeline (after Researcher).
    """
    print("\n[Distiller] Distilling research context...")
    
    context = state.get("research_context")
    if not context:
        print("[Distiller] No research context found. Skipping distillation.")
        return state
    
    llm = _get_llm()
    if not llm:
        print("[Distiller] No API key. Skipping.")
        return state

    print(f"[Distiller] Using model: {llm.model}")
    
    prompt = PromptTemplate(
        template="""\
你是一位 "信息提取专家" (Information Distiller)。
你的任务是从以下原始搜索结果中提取最关键的信息，去除噪音，并生成一断简练的 "背景摘要"。
这段摘要将被用于辅助 "战略架构师" 更好地理解问题背景并制定方案。

原始问题: {problem}

搜索结果:
{context}

请生成一段不超过 500 字的中文摘要，重点包含:
1. 核心定义与关键事实。
2. 现有解决方案的优缺点。
3. 任何可能影响战略制定的约束或机会。

摘要:
""",
        input_variables=["problem", "context"]
    )
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        summary = chain.invoke({
            "problem": state["problem_state"],
            "context": context
        })
        
        print(f"[Distiller] Distilled summary length: {len(summary)} chars.")
        
        # Inject into problem state
        new_problem_state = f"{state['problem_state']}\n\n[背景补充]:\n{summary}"
        
        return {
            **state,
            "problem_state": new_problem_state,
            "research_context": summary,
            "history": state.get("history", []) + ["Distiller refined context"]
        }
        
    except Exception as e:
        print(f"[Distiller] Error: {e}")
        return state


def generate_judge_context(state: DeepThinkState) -> str:
    """
    Generate a clean, summarized context for Judge to use in experience evaluation.
    
    This function creates a "pure" context that prevents context rot by:
    1. Summarizing strategies status (not raw data)
    2. Summarizing recent history (not full log)
    3. Providing key metrics in readable form
    
    Returns:
        A clean markdown-formatted context string for Judge
    """
    lines = []
    
    # 1. Problem summary (first 200 chars)
    problem = state.get("problem_state", "")
    if "[背景补充]" in problem:
        # Extract just the original problem
        problem = problem.split("[背景补充]")[0].strip()
    lines.append(f"## 问题概述\n{problem[:300]}...")
    
    # 2. Current iteration metrics
    lines.append(f"\n## 当前状态")
    lines.append(f"- 迭代次数: {state.get('iteration_count', 0)}")
    lines.append(f"- 系统温度 (τ): {state.get('normalized_temperature', 0):.3f}")
    lines.append(f"- 空间熵: {state.get('spatial_entropy', 0):.4f}")
    
    # 3. Strategies summary
    strategies = state.get("strategies", [])
    lines.append(f"\n## 策略概览")
    lines.append(_summarize_strategies(strategies))
    
    # 4. Recent history
    history = state.get("history", [])
    lines.append(f"\n## 最近事件")
    lines.append(_summarize_history(history))
    
    return "\n".join(lines)


def distiller_for_judge_node(state: DeepThinkState) -> DeepThinkState:
    """
    Distiller node that runs BEFORE Judge to prepare clean context.
    
    This creates a 'judge_context' field with a summarized, non-rotting
    view of the current state for Judge's experience evaluation.
    """
    print("\n[Distiller] Preparing context for Judge...")
    
    # Generate clean context summary
    judge_context = generate_judge_context(state)
    
    print(f"[Distiller] Judge context prepared ({len(judge_context)} chars)")
    
    return {
        **state,
        "judge_context": judge_context,
    }

