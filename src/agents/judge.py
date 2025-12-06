
import os
from typing import List

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.state import DeepThinkState, StrategyNode

def judge_node(state: DeepThinkState) -> DeepThinkState:
    """
    Evaluates the feasibility of active strategies.
    Prunes strategies that are deemed logically incoherent or violated constraints.
    """
    print("\n[Judge] Evaluating strategy feasibility...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[Judge] Error: GEMINI_API_KEY not set. Skipping evaluation.")
        return state

    strategies = state["strategies"]
    active_indices = [i for i, s in enumerate(strategies) if s["status"] == "active"]
    
    if not active_indices:
        print("[Judge] No active strategies to evaluate.")
        return state

    llm = ChatGoogleGenerativeAI(
        model="models/gemini-flash-latest",
        google_api_key=api_key,
        temperature=0.1, # Low temperature for objective evaluation
    )

    parser = JsonOutputParser()

    prompt_template = """\
你是一位严格的 "战略审查官" (Judge Agent)。
你的任务是评估以下战略方案的可行性与逻辑自洽性。

问题背景:
{problem_state}

战略方案 "{strategy_name}":
理由: {rationale}
关键假设: {initial_assumption}

请基于以下标准进行打分 (0-10) 并给出简短评语:
1. 逻辑自洽性: 理由是否支持结论？
2. 假设合理性: 关键假设是否过于牵强？
3. 约束符合性: 是否违背了基本的物理或逻辑约束？

注意: 你不需要验证外部事实的真伪 (Hallucination is accepted limitation)，仅关注逻辑层面的可行性。

输出格式 JSON:
{{
    "feasibility_score": float, // 0.0 到 10.0
    "reasoning": "简短评语",
    "is_pruned": boolean // 如果分数 < 4.0 或存在致命逻辑漏洞，设为 true
}}
"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["problem_state", "strategy_name", "rationale", "initial_assumption"]
    )
    
    chain = prompt | llm | parser

    evaluated_count = 0
    pruned_count = 0
    
    new_strategies = list(strategies) # Shallow copy to modify

    for idx in active_indices:
        strategy = strategies[idx]
        
        # Skip if already scored (optional optimization)
        # For now, we assume Judge runs once per generation
        
        try:
            result = chain.invoke({
                "problem_state": state["problem_state"],
                "strategy_name": strategy["name"],
                "rationale": strategy["rationale"],
                "initial_assumption": strategy["assumption"]
            })
            
            score = float(result.get("feasibility_score", 5.0))
            is_pruned = result.get("is_pruned", False)
            reasoning = result.get("reasoning", "")
            
            # Simple logic: Update history/trajectory
            new_strategies[idx]["trajectory"] = strategy.get("trajectory", []) + [
                f"[Judge] Score: {score}, Pruned: {is_pruned}, Reasoning: {reasoning}"
            ]
            
            # Store base score (normalized to 0-1 for UCB later?) 
            # UCB usually expects 0-1. Let's normalize 0-10 -> 0-1.
            # But we serve this as 'value' V.
            new_strategies[idx]["score"] = score / 10.0 
            
            if is_pruned:
                new_strategies[idx]["status"] = "pruned"
                pruned_count += 1
            
            evaluated_count += 1
            print(f"  > '{strategy['name']}' Score: {score}, Pruned: {is_pruned}")
            
        except Exception as e:
            print(f"[Judge] Error evaluating strategy {strategy['name']}: {e}")
            
    print(f"[Judge] Evaluated {evaluated_count} strategies. Pruned {pruned_count}.")
    
    return {
        **state,
        "strategies": new_strategies,
        "history": state.get("history", []) + [f"Judge evaluated {evaluated_count}, pruned {pruned_count}"]
    }
