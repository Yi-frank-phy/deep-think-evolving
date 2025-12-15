"""
Propagation Agent - 策略传播器

基于 Evolution 分配的 child_quota，为每个策略生成子节点。
这是演化过程中创建新策略的核心机制。

设计理念：
- child_quota 由 Boltzmann 分配决定
- 每个子节点是父策略的"变体"或"深化"方向
- parent_id 建立树结构，支持图状演化可视化
"""

import os
import uuid
from typing import List, Dict, Any

from google import genai
from google.genai import types
import json

from src.core.state import DeepThinkState, StrategyNode


PROPAGATION_PROMPT = """\
你是一位"策略演化专家"，负责基于已有策略生成变体方向。

## 原始问题
{problem}

## 父策略信息
- 名称: {parent_name}
- 理由: {parent_rationale}
- 假设: {parent_assumption}
- 当前评分: {parent_score}
- UCB分数: {parent_ucb}

## 父策略执行轨迹
{parent_trajectory}

## 任务
为这个父策略生成 **{num_children}** 个不同的子策略方向。

每个子策略应该是父策略的：
- **变体**: 保留核心思路，但尝试不同的实现路径
- **深化**: 在某个特定方面进行更深入的探索
- **分支**: 基于父策略的洞见，探索新的可能性

## 约束
1. 子策略必须与父策略相关，但不能完全重复
2. 子策略之间应该有足够的差异性
3. 保持策略的高层次性，不要过于具体

## 输出格式 (严格 JSON 数组)
[
    {{
        "strategy_name": "子策略名称",
        "rationale": "详细的策略理由（完整描述，不要截断）",
        "initial_assumption": "核心假设"
    }}
]
"""


def generate_children_for_strategy(
    problem: str,
    parent: StrategyNode,
    num_children: int,
    api_key: str,
    use_mock: bool = False,
    thinking_budget: int = 1024  # 新增: 思考预算
) -> List[StrategyNode]:
    """
    为单个父策略生成子策略。
    
    Args:
        problem: 原始问题
        parent: 父策略节点
        num_children: 要生成的子节点数量
        api_key: API key
        use_mock: 是否使用 Mock 模式
        
    Returns:
        子策略节点列表
    """
    if num_children <= 0:
        return []
    
    if use_mock:
        children = []
        for i in range(num_children):
            child: StrategyNode = {
                "id": str(uuid.uuid4()),
                "name": f"{parent['name']} - 变体{i+1}",
                "rationale": f"基于父策略 '{parent['name']}' 的第 {i+1} 个变体方向。",
                "assumption": f"继承自: {parent.get('assumption', '')}",
                "milestones": [],
                "embedding": None,
                "density": None,
                "log_density": None,
                "score": 0.0,
                "ucb_score": None,
                "child_quota": 0,
                "status": "active",
                "trajectory": [f"[Propagation] 由 '{parent['name']}' 分支生成"],
                "parent_id": parent["id"],
                "pruned_at_report_version": None,
                "full_response": f"Mock 变体策略，继承自 {parent['name']}",
                "thinking_summary": f"由父策略分支生成"
            }
            children.append(child)
        return children
    
    # 构建 Prompt
    trajectory_str = "\n".join(parent.get("trajectory", [])[-5:]) or "(无执行记录)"
    
    prompt = PROPAGATION_PROMPT.format(
        problem=problem,
        parent_name=parent.get("name", "Unknown"),
        parent_rationale=parent.get("rationale", ""),
        parent_assumption=parent.get("assumption", ""),
        parent_score=parent.get("score", 0),
        parent_ucb=parent.get("ucb_score", 0),
        parent_trajectory=trajectory_str,
        num_children=num_children
    )
    
    # 调用 LLM
    client = genai.Client(api_key=api_key)
    
    model_name = os.environ.get(
        "GEMINI_MODEL_GENERATOR",
        os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    )
    
    # 决策类 Agent: JSON 输出 + thinking_budget，不需要 Grounding
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
    )
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        
        raw_strategies = json.loads(response.text)
        if not isinstance(raw_strategies, list):
            raw_strategies = [raw_strategies]
            
    except Exception as e:
        print(f"[Propagation] Error generating children: {e}")
        return []
    
    # 转换为 StrategyNode
    children = []
    for raw in raw_strategies[:num_children]:  # 限制数量
        if not isinstance(raw, dict):
            continue
        if not raw.get("strategy_name"):
            continue
            
        child: StrategyNode = {
            "id": str(uuid.uuid4()),
            "name": raw.get("strategy_name", "Unnamed"),
            "rationale": raw.get("rationale", ""),
            "assumption": raw.get("initial_assumption", ""),
            "milestones": [],
            "embedding": None,
            "density": None,
            "log_density": None,
            "score": 0.0,
            "ucb_score": None,
            "child_quota": 0,
            "status": "active",
            "trajectory": [f"[Propagation] 由 '{parent['name']}' 分支生成"],
            "parent_id": parent["id"],
            "pruned_at_report_version": None,
            "full_response": raw.get("rationale", ""),
            "thinking_summary": f"由父策略 '{parent['name']}' 分支生成。假设: {raw.get('initial_assumption', '')}"
        }
        children.append(child)
    
    return children


def propagation_node(state: DeepThinkState) -> DeepThinkState:
    """
    Propagation Node - 策略传播器
    
    基于 Evolution 分配的 child_quota，为每个策略生成子节点。
    这是建立策略树/图结构的关键节点。
    """
    print("\n[Propagation] Generating child strategies based on quotas...")
    
    strategies = state.get("strategies", [])
    problem = state["problem_state"]
    
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key
    
    if use_mock:
        print("[Propagation] Running in MOCK MODE.")
    
    # 收集所有需要生成子节点的策略
    new_children: List[StrategyNode] = []
    expanded_count = 0
    
    for strategy in strategies:
        if strategy.get("status") != "active":
            continue
            
        quota = strategy.get("child_quota", 0)
        if quota <= 0:
            continue
        
        print(f"  > Generating {quota} children for '{strategy['name']}'...")
        
        # 从 config 获取 thinking_budget
        config = state.get("config", {})
        thinking_budget = config.get("thinking_budget", 1024)
        
        children = generate_children_for_strategy(
            problem=problem,
            parent=strategy,
            num_children=quota,
            api_key=api_key,
            use_mock=use_mock,
            thinking_budget=thinking_budget
        )
        
        if children:
            new_children.extend(children)
            # 标记父节点为已扩展，并清除 quota 防止重复扩展
            strategy["status"] = "expanded"
            strategy["child_quota"] = 0  # 防止无限扩展
            expanded_count += 1
            print(f"    Created {len(children)} children")
    
    # 合并新子策略到策略池
    all_strategies = strategies + new_children
    
    print(f"[Propagation] Expanded {expanded_count} strategies, created {len(new_children)} children.")
    print(f"[Propagation] Total strategies: {len(all_strategies)}")
    
    return {
        **state,
        "strategies": all_strategies,
        "history": state.get("history", []) + [
            f"Propagation: {expanded_count} expanded, {len(new_children)} children created"
        ]
    }
