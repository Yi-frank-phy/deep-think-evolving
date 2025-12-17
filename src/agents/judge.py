
import json
import os
import re
from typing import List, Optional

from google import genai
from google.genai import types

from src.core.state import DeepThinkState, StrategyNode
from src.tools.knowledge_base import write_experience

# System prompt for Judge with knowledge base awareness
JUDGE_SYSTEM_PROMPT = """\
你是一位经验丰富的 "战略审查官" (Judge Agent)，负责：
1. 评估战略方案的可行性与逻辑自洽性
2. 给出客观评分 (0-10)

## 知识库写入原则 (极度谨慎)

⚠️ 只有在发现了**可泛化到未来问题**的抽象经验时才调用 write_experience。

不要写入:
- 具体问题的具体答案 (这会污染未来问题)
- 每个策略的评估结果 (这是正常流程，不需要记录)
- 与当前问题高度相关但不可泛化的洞见

可以写入 (每次运行最多1-2条，通常为0):
- 反复出现的**推理模式错误** (元层面的教训)
- 可应用于**任何领域**的分支决策启发
- 关于**如何评估假设**的元策略
"""


def judge_node(state: DeepThinkState) -> DeepThinkState:
    """
    Evaluates the feasibility of active strategies.
    
    Enhanced with knowledge base capabilities:
    - Uses distilled judge_context from Distiller (prevents context rot)
    - Can write lessons learned and success patterns
    - Has full context of strategy evolution for reflection
    """
    print("\n[Judge] Evaluating strategy feasibility...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key
    
    if not api_key and not use_mock:
        print("[Judge] Error: GEMINI_API_KEY not set. Skipping evaluation.")
        return state

    strategies = state["strategies"]
    active_indices = [i for i, s in enumerate(strategies) if s.get("status") == "active"]
    
    if not active_indices:
        print("[Judge] No active strategies to evaluate.")
        return state

    # Initialize LLM only if not in mock mode
    client = None
    
    if not use_mock:
        model_name = os.environ.get("GEMINI_MODEL_JUDGE", os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"))
        print(f"[Judge] Using model: {model_name}")
        
        # 从 config 读取 thinking_budget
        config_data = state.get("config", {})
        thinking_budget = config_data.get("thinking_budget", 1024)
        
        # Initialize client
        client = genai.Client(api_key=api_key)
        
        # Create tools list
        # We pass the raw function `write_experience` which google.genai can inspect
        tools = [write_experience]
        
        # Config with thinking and tools
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            tools=tools,
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
            temperature=0.1 # Low temperature for objective evaluation
        )

    # Get distilled context from Distiller (prevents context rot)
    judge_context = state.get("judge_context", "")
    if not judge_context:
        # Fallback if distiller didn't run
        judge_context = f"问题: {state.get('problem_state', '')[:200]}..."
        print("[Judge] Warning: No distilled judge_context found, using fallback.")

    # Enhanced prompt using DISTILLED context
    EVALUATION_PROMPT_TEMPLATE = """\
{system_prompt}

{judge_context}

---

## 待评估策略 "{strategy_name}"
理由: {rationale}
关键假设: {initial_assumption}
历史轨迹:
{trajectory}

---

## 评估任务

请基于以下标准进行打分 (0-10) 并给出简短评语:
1. 逻辑自洽性: 理由是否支持结论？
2. 假设合理性: 关键假设是否过于牵强？
3. 约束符合性: 是否违背了基本的物理或逻辑约束？

在评估过程中，请结合上述"策略概览"和"最近事件"，判断是否存在值得记录的教训或成功模式。
如果发现值得记录的经验，请调用 write_experience 工具。

注意：你只负责评分，不负责决定策略的去留。资源分配由系统的 Boltzmann 软剪枝机制自动决定。

输出格式 JSON:
{{
    "feasibility_score": float, // 0.0 到 10.0
    "reasoning": "简短评语"
}}
"""

    evaluated_count = 0
    kb_writes = 0
    
    if use_mock:
        print("[Judge] Running in MOCK MODE.")
        import random

    new_strategies = list(strategies)  # Shallow copy to modify
    
    # Build trajectory string for context
    def format_trajectory(traj: List[str]) -> str:
        if not traj:
            return "(无历史记录)"
        return "\n".join([f"  - {step}" for step in traj[-5:]])  # Last 5 steps

    for idx in active_indices:
        strategy = strategies[idx]
        
        try:
            if not use_mock:
                prompt = EVALUATION_PROMPT_TEMPLATE.format(
                    system_prompt=JUDGE_SYSTEM_PROMPT,
                    judge_context=judge_context,
                    strategy_name=strategy["name"],
                    rationale=strategy["rationale"],
                    initial_assumption=strategy["assumption"],
                    trajectory=format_trajectory(strategy.get("trajectory", []))
                )
                
                # Call LLM
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                
                # Check for tool calls (function calls) in response parts
                if response.function_calls:
                    for call in response.function_calls:
                        if call.name == 'write_experience':
                            try:
                                # Convert MapComposite to dict
                                args = {k: v for k, v in call.args.items()}
                                result = write_experience(**args)
                                print(f"  [KB] {result}")
                                kb_writes += 1
                            except Exception as e:
                                print(f"  [KB Error] {e}")
                
                # Parse the JSON content
                try:
                    content = response.text
                    result = json.loads(content)
                except (json.JSONDecodeError, ValueError, AttributeError) as parse_err:
                    # Fallback: try to extract score from text if response.text is not pure JSON (though response_mime_type should help)
                    print(f"  [Judge] Warning: JSON parse failed for {strategy['name']}: {parse_err}")
                    # Try to extract numeric score from response text using regex
                    score_match = re.search(r'feasibility_score["\s:]+(\d+(?:\.\d+)?)', str(response.text))
                    if score_match:
                        extracted_score = float(score_match.group(1))
                        result = {"feasibility_score": extracted_score, "reasoning": "Score extracted from response"}
                        print(f"  [Judge] Extracted score: {extracted_score}")
                    else:
                        result = {"feasibility_score": 5.0, "reasoning": "Evaluation completed (parse fallback)"}
                
                score = float(result.get("feasibility_score", 5.0))
                reasoning = result.get("reasoning", "")
            else:
                # Mock Logic
                score = random.uniform(4.0, 9.5)
                reasoning = "Mock evaluation: Assessment completed."
            
            # Update trajectory (no pruning decision - only scoring)
            new_strategies[idx]["trajectory"] = strategy.get("trajectory", []) + [
                f"[Judge] Score: {score:.2f}, Reasoning: {reasoning}"
            ]
            
            # Normalize score to 0-1 for UCB
            new_strategies[idx]["score"] = score / 10.0
            # No hard pruning - Boltzmann allocation decides resource distribution
            
            evaluated_count += 1
            print(f"  > '{strategy['name']}' Score: {score:.2f}")
            
        except Exception as e:
            print(f"[Judge] Error evaluating strategy {strategy['name']}: {e}")
            import traceback
            traceback.print_exc()
            
    print(f"[Judge] Evaluated {evaluated_count} strategies. KB writes: {kb_writes}.")
    
    return {
        **state,
        "strategies": new_strategies,
        "history": state.get("history", []) + [
            f"Judge evaluated {evaluated_count} strategies, KB writes: {kb_writes}"
        ]
    }
