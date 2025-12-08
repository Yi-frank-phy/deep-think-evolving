"""
Executor Agent - 策略执行器

执行 Architect 分配的具体任务。共享 Executor 池按需分配。
可以：生成策略变体、直接探索策略方向、验证假设等。
所有 Agent 都有 Grounding 能力，这不是某个 Agent 的特权。
"""

import os
import uuid
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.state import DeepThinkState, StrategyNode


EXECUTOR_PROMPT_TEMPLATE = """\
你是一位"策略执行专家"，拥有 Google Search Grounding 工具能力（如需要可以搜索外部信息）。

## 原始问题
{problem}

## 你负责的策略
- 策略名称: {strategy_name}
- 策略理由: {strategy_rationale}
- 核心假设: {strategy_assumption}

## Architect 的执行指令
{executor_instruction}

## 额外参考上下文
{context_injection}

## 任务
请根据 Architect 的指令执行任务。你的输出应该是对策略的具体推进，可能包括：
- 对策略的进一步细化
- 生成策略的变体方向
- 验证核心假设的分析
- 识别潜在风险和机会

## 输出格式 (严格 JSON)
{{
    "execution_result": "执行结果的详细描述",
    "new_insights": ["洞见1", "洞见2"],
    "next_steps": ["建议的后续步骤1", "建议的后续步骤2"],
    "variant_strategy": {{  // 可选：如果生成了变体策略
        "strategy_name": "变体策略名称",
        "rationale": "变体策略理由",
        "initial_assumption": "变体策略假设"
    }}
}}
"""


def execute_single_task(
    problem: str,
    strategy: StrategyNode,
    decision: Dict[str, Any],
    api_key: str,
    use_mock: bool = False
) -> Dict[str, Any]:
    """
    Execute a single task for a strategy based on Architect's decision.
    
    Args:
        problem: Original problem statement
        strategy: The strategy to work on
        decision: Architect's decision containing executor_instruction and context_injection
        api_key: API key for LLM
        use_mock: Whether to run in mock mode
        
    Returns:
        Execution result dictionary
    """
    if use_mock:
        return {
            "execution_result": f"Mock execution for {strategy['name']}: Task completed successfully.",
            "new_insights": ["Mock insight 1", "Mock insight 2"],
            "next_steps": ["Continue exploration", "Validate assumption"],
            "variant_strategy": None
        }
    
    # Initialize client with grounding
    client = genai.Client(api_key=api_key)
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    
    model_name = os.environ.get(
        "GEMINI_MODEL_EXECUTOR",
        os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    )
    
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        response_mime_type="application/json"
    )
    
    prompt = EXECUTOR_PROMPT_TEMPLATE.format(
        problem=problem,
        strategy_name=strategy.get("name", ""),
        strategy_rationale=strategy.get("rationale", ""),
        strategy_assumption=strategy.get("assumption", ""),
        executor_instruction=decision.get("executor_instruction", "探索此策略方向"),
        context_injection=decision.get("context_injection", "无额外上下文")
    )
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        
        import json
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            result = {
                "execution_result": response.text,
                "new_insights": [],
                "next_steps": [],
                "variant_strategy": None
            }
        
        return result
        
    except Exception as e:
        print(f"[Executor] Error executing task: {e}")
        return {
            "execution_result": f"Error: {str(e)}",
            "new_insights": [],
            "next_steps": [],
            "variant_strategy": None
        }


def executor_node(state: DeepThinkState) -> DeepThinkState:
    """
    Executor Node - 策略执行器
    
    基于 Architect 的决策，对每个策略执行相应任务。
    共享 Executor 池按需分配，每次调用是独立的 API 请求。
    """
    print("\n[Executor] Executing tasks based on Architect decisions...")
    
    architect_decisions = state.get("architect_decisions", [])
    strategies = state.get("strategies", [])
    problem = state["problem_state"]
    
    if not architect_decisions:
        print("[Executor] No Architect decisions to execute.")
        return state
    
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key
    
    if use_mock:
        print("[Executor] Running in MOCK MODE.")
    
    # Create strategy lookup
    strategy_map = {s["id"]: s for s in strategies}
    
    new_strategies: List[StrategyNode] = []
    executed_count = 0
    
    for decision in architect_decisions:
        strategy_id = decision.get("strategy_id")
        if not strategy_id or strategy_id not in strategy_map:
            continue
            
        strategy = strategy_map[strategy_id]
        
        print(f"  > Executing for '{strategy['name']}'...")
        
        # Execute the task
        result = execute_single_task(
            problem=problem,
            strategy=strategy,
            decision=decision,
            api_key=api_key,
            use_mock=use_mock
        )
        
        # Update strategy trajectory
        strategy["trajectory"] = strategy.get("trajectory", []) + [
            f"[Executor] {result.get('execution_result', 'Task executed')[:100]}..."
        ]
        
        # If a variant strategy was generated, add it
        variant = result.get("variant_strategy")
        if variant and isinstance(variant, dict) and variant.get("strategy_name"):
            new_node: StrategyNode = {
                "id": str(uuid.uuid4()),
                "name": variant.get("strategy_name", "Variant"),
                "rationale": variant.get("rationale", ""),
                "assumption": variant.get("initial_assumption", ""),
                "milestones": [],
                "embedding": None,
                "density": None,
                "log_density": None,
                "score": 0.0,
                "status": "active",
                "trajectory": [f"[Executor] Generated as variant of {strategy['name']}"],
                "parent_id": strategy["id"]
            }
            new_strategies.append(new_node)
            print(f"    Created variant: '{new_node['name']}'")
        
        executed_count += 1
    
    # Merge new strategies with existing
    all_strategies = strategies + new_strategies
    
    print(f"[Executor] Executed {executed_count} tasks, created {len(new_strategies)} variants.")
    
    return {
        **state,
        "strategies": all_strategies,
        "architect_decisions": [],  # Clear decisions after execution
        "history": state.get("history", []) + [
            f"Executor: {executed_count} tasks, {len(new_strategies)} variants"
        ]
    }
