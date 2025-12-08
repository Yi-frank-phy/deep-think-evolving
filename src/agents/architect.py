"""
Architect Agent - 战略调度官 (UCB 驱动的执行调度器)

重构后的 Architect 不再生成策略（由 StrategyGenerator 负责），
而是基于 UCB 评分为每个策略编写执行指令，分配给 Executor 执行。

设计理念：不存在硬编码的 explore/variant/skip 模式。
Architect 通过自然语言指令自由引导 Executor，指令内容完全由 Architect 自主决定。
"""

import os
import json
from typing import List, Dict, Any

from google import genai
from google.genai import types
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.state import DeepThinkState, StrategyNode


ARCHITECT_SCHEDULER_PROMPT = """\
你是一位"战略调度官" (Architect)，拥有 Google Search Grounding 工具能力（如需要可以搜索外部信息）。

## 你的职责
1. 基于 UCB 评分和你的判断，为每个策略编写执行指令
2. 可选择向 Executor 传递相关上下文以辅助执行
3. 你可以自由决定让 Executor 如何处理每个策略（直接探索、生成变体、深化某个方向、验证假设等）

## 原始问题
{problem}

## 当前策略 (按 UCB 排序，已由 Boltzmann 分配筛选)
{ranked_strategies}

## 你的任务
为每个策略编写具体的执行指令。指令应该清晰、原子化，告诉 Executor 具体要做什么。

你可以：
- 让 Executor 直接探索策略方向
- 让 Executor 生成该策略的变体
- 让 Executor 深化某个具体方面
- 让 Executor 验证核心假设
- 任何你认为合适的任务

## 输出格式 (严格 JSON 数组)
[
    {{
        "strategy_id": "策略ID",
        "executor_instruction": "具体的执行指令（自然语言描述任务）",
        "context_injection": "可选：传递给 Executor 的相关背景信息"
    }}
]
"""


def _format_strategies_for_prompt(strategies: List[StrategyNode]) -> str:
    """Format strategies with UCB scores for the prompt."""
    # Sort by UCB score (or regular score if UCB not available)
    sorted_strategies = sorted(
        strategies,
        key=lambda s: s.get("ucb_score", s.get("score", 0)),
        reverse=True
    )
    
    lines = []
    for i, s in enumerate(sorted_strategies, 1):
        score = s.get("score", 0)
        ucb = s.get("ucb_score", score)
        quota = s.get("child_quota", 0)
        lines.append(
            f"{i}. [{s['id'][:8]}...] {s['name']}\n"
            f"   UCB: {ucb:.3f}, Score: {score:.3f}, 配额: {quota}\n"
            f"   理由: {s.get('rationale', '')[:100]}...\n"
            f"   假设: {s.get('assumption', '')[:80]}..."
        )
    
    return "\n\n".join(lines)


def architect_scheduler_node(state: DeepThinkState) -> DeepThinkState:
    """
    Architect Scheduler Node - 战略调度官
    
    基于 UCB 评分和 Boltzmann 分配，为每个有配额的策略编写执行指令。
    不再生成策略（由 StrategyGenerator 负责）。
    """
    print("\n[Architect] Scheduling execution tasks based on UCB scores...")
    
    strategies = state.get("strategies", [])
    problem = state["problem_state"]
    
    # Filter to only active strategies with child_quota > 0 (from Boltzmann allocation)
    active_strategies = [
        s for s in strategies 
        if s.get("status") == "active" and s.get("child_quota", 0) > 0
    ]
    
    if not active_strategies:
        print("[Architect] No active strategies with allocation to schedule.")
        return {
            **state,
            "architect_decisions": [],
            "history": state.get("history", []) + ["Architect: no strategies to schedule"]
        }
    
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key
    
    if use_mock:
        print("[Architect] Running in MOCK MODE.")
        decisions = [
            {
                "strategy_id": s["id"],
                "executor_instruction": f"探索策略 '{s['name']}' 的核心方向，尝试识别关键的实施步骤。",
                "context_injection": f"该策略的核心假设是: {s.get('assumption', '未知')}"
            }
            for s in active_strategies
        ]
    else:
        model_name = os.environ.get(
            "GEMINI_MODEL_ARCHITECT",
            os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        )
        print(f"[Architect] Using model: {model_name}")
        
        # Initialize client with grounding
        client = genai.Client(api_key=api_key)
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        
        config = types.GenerateContentConfig(
            tools=[grounding_tool],
            response_mime_type="application/json"
        )
        
        prompt = ARCHITECT_SCHEDULER_PROMPT.format(
            problem=problem,
            ranked_strategies=_format_strategies_for_prompt(active_strategies)
        )
        
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            
            try:
                decisions = json.loads(response.text)
                if not isinstance(decisions, list):
                    decisions = [decisions]
            except json.JSONDecodeError:
                print("[Architect] Failed to parse response, using fallback.")
                decisions = [
                    {
                        "strategy_id": s["id"],
                        "executor_instruction": "继续探索此策略方向",
                        "context_injection": ""
                    }
                    for s in active_strategies
                ]
                
        except Exception as e:
            print(f"[Architect] Error: {e}")
            decisions = []
    
    print(f"[Architect] Created {len(decisions)} execution decisions.")
    
    for d in decisions[:3]:  # Print first 3
        sid = d.get("strategy_id", "?")[:8]
        instr = d.get("executor_instruction", "")[:50]
        print(f"  > [{sid}...] {instr}...")
    
    return {
        **state,
        "architect_decisions": decisions,
        "history": state.get("history", []) + [
            f"Architect: scheduled {len(decisions)} execution tasks"
        ]
    }


# Legacy function for backward compatibility
def strategy_architect_node(state: DeepThinkState) -> DeepThinkState:
    """
    Legacy wrapper - redirects to StrategyGenerator for initial generation.
    
    DEPRECATED: Use strategy_generator_node for initial generation
    and architect_scheduler_node for execution scheduling.
    """
    print("[Architect] WARNING: Using legacy strategy_architect_node. Consider using new flow.")
    
    # Import here to avoid circular import
    from src.agents.strategy_generator import strategy_generator_node
    return strategy_generator_node(state)
