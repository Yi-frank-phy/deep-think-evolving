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

from src.core.state import DeepThinkState, StrategyNode


ARCHITECT_SCHEDULER_PROMPT = """\
你是一位"战略调度官" (Architect)，拥有 Google Search Grounding 工具能力（如需要可以搜索外部信息）。

## 元策略框架 (Meta-Strategy)

你的任务不是从预设选项中选择，而是基于以下战略思考框架自由制定执行指令：

**探索 ↔ 利用 ↔ 综合** 形成一个连续的频谱，没有硬编码边界。

- **探索倾向** (Exploration): 当策略空间分散、温度高、熵变化大时，适合发散探索新方向
- **利用倾向** (Exploitation): 当有高分策略、温度低时，适合深化验证已有发现
- **综合倾向** (Synthesis): 当策略成熟、熵趋于稳定时，适合整合发现形成阶段性报告

你可以在同一轮中混合使用这些倾向，也可以创造不属于以上任何类别的任务。
这只是一个思考框架，具体如何执行完全由你自主决定。

## 系统状态

- 归一化温度 τ: {normalized_temperature:.3f} (0=冷/收敛, 1=热/发散)
- 空间熵: {spatial_entropy:.4f}
- 当前迭代: {iteration_count}
- 已有报告版本: {report_version}

## 原始问题
{problem}

## 当前策略 (按 UCB 排序，已由 Boltzmann 分配筛选)
{ranked_strategies}

## 你的任务

为当前状态制定执行指令。你可以：
- 为某个策略编写探索/深化指令
- 为多个策略编写综合对比指令
- 编写阶段性报告生成指令（当你判断时机合适时）
- 任何你认为对解决问题有帮助的任务

指令应该是清晰的自然语言，告诉 Executor 具体要做什么。

## ⚠️ 综合任务的硬剪枝机制

当 strategy_id 为 null（综合任务）时，**所有活跃策略将被硬剪枝**。
这是一个不可逆操作，但价值通过以下方式保留：
1. 报告本身 - 综合的结论和洞见
2. 知识库 - 分支选择逻辑、推理过程存入向量数据库

建议在 **温度足够低 + 策略足够成熟** 时再触发综合任务。

## 输出格式 (严格 JSON 数组)
[
    {{
        "strategy_id": "策略ID，或 null 表示综合任务（触发硬剪枝）",
        "executor_instruction": "自由编写的执行指令（自然语言）",
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
            f"   理由: {s.get('rationale', '')}\n"
            f"   假设: {s.get('assumption', '')}"
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
        
        # 决策类 Agent: JSON 输出 + thinking_budget，不需要 Grounding
        client = genai.Client(api_key=api_key)
        
        # 从 config 读取 thinking_budget
        config_data = state.get("config", {})
        thinking_budget = config_data.get("thinking_budget", 1024)
        
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
        )
        
        prompt = ARCHITECT_SCHEDULER_PROMPT.format(
            problem=problem,
            ranked_strategies=_format_strategies_for_prompt(active_strategies),
            normalized_temperature=state.get("normalized_temperature", 0.5),
            spatial_entropy=state.get("spatial_entropy", 0.0),
            iteration_count=state.get("iteration_count", 0),
            report_version=state.get("report_version", 0)
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
