
import os
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.state import DeepThinkState, StrategyNode
from src.tools.knowledge_base import write_experience, search_experiences


# System prompt for Judge with knowledge base awareness
JUDGE_SYSTEM_PROMPT = """\
你是一位经验丰富的 "战略审查官" (Judge Agent)，负责：
1. 评估战略方案的可行性与逻辑自洽性
2. 观察策略演化过程中的规律和教训
3. 在发现值得记录的经验时，主动写入知识库

## 你的知识库写入指南

当你观察到以下情况时，应该调用 write_experience 工具记录：

🔴 **教训 (lesson_learned)**:
- 某个策略因为逻辑漏洞被剪枝，该漏洞模式可能在未来重复出现
- 发现一类假设总是过于乐观或悲观
- 某种推理链条在实践中反复失败

🟢 **成功模式 (success_pattern)**:
- 某个策略的推理方式特别清晰有效
- 某种假设设计在多个场景下都表现良好
- 发现了问题分解的有效方法

💡 **洞见 (insight)**:
- 在评估过程中发现了问题的新视角
- 总结出某类问题的共同特征
- 识别出策略之间的隐含关联

你不需要为每个策略都写入知识库，只在真正有价值的洞见出现时才记录。
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
    llm = None
    llm_with_tools = None
    parser = None
    
    if not use_mock:
        model_name = os.environ.get("GEMINI_MODEL_JUDGE", os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
        print(f"[Judge] Using model: {model_name}")
        
        # Create LLM with tool binding for knowledge base
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1,  # Low temperature for objective evaluation
        )
        
        # Bind knowledge base tools
        llm_with_tools = llm.bind_tools([write_experience])
        parser = JsonOutputParser()

    # Get distilled context from Distiller (prevents context rot)
    judge_context = state.get("judge_context", "")
    if not judge_context:
        # Fallback if distiller didn't run
        judge_context = f"问题: {state.get('problem_state', '')[:200]}..."
        print("[Judge] Warning: No distilled judge_context found, using fallback.")

    # Enhanced prompt using DISTILLED context
    evaluation_prompt = ChatPromptTemplate.from_messages([
        ("system", JUDGE_SYSTEM_PROMPT),
        ("human", """\
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
""")])

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
                # Invoke with tool support
                messages = evaluation_prompt.format_messages(
                    judge_context=judge_context,
                    strategy_name=strategy["name"],
                    rationale=strategy["rationale"],
                    initial_assumption=strategy["assumption"],
                    trajectory=format_trajectory(strategy.get("trajectory", []))
                )
                
                response = llm_with_tools.invoke(messages)
                
                # Check for tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        if tool_call['name'] == 'write_experience':
                            try:
                                result = write_experience.invoke(tool_call['args'])
                                print(f"  [KB] {result}")
                                kb_writes += 1
                            except Exception as e:
                                print(f"  [KB Error] {e}")
                
                # Parse the JSON content
                try:
                    result = parser.parse(response.content)
                except:
                    # Fallback if JSON parsing fails
                    result = {"feasibility_score": 5.0, "reasoning": "Evaluation completed"}
                
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
