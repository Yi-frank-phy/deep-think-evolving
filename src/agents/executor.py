"""
Executor Agent - 策略执行器

执行 Architect 分配的具体任务。共享 Executor 池按需分配。
可以：
- 生成策略变体
- 直接探索策略方向
- 验证假设
- 综合多策略生成阶段性报告（当 strategy_id 为 null 时）

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
from src.tools.knowledge_base import write_strategy_archive



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


# Prompt template for synthesis/report tasks (strategy_id is null)
SYNTHESIS_PROMPT_TEMPLATE = """\
你是一位"研究综合专家"，拥有 Google Search Grounding 工具能力（如需要可以搜索外部信息）。

## 原始问题
{problem}

## Architect 的综合指令
{executor_instruction}

## ⚠️ 重要：硬剪枝通知

以下策略将在报告生成后被**硬剪枝**（永久移除出活跃策略池）：

{strategies_to_prune}

**你必须确保报告完整包含这些策略的所有有价值内容：**
- 核心思路和推理过程
- 关键假设和验证结果
- 成功经验和失败教训
- 分支选择的逻辑和原因
- 任何值得保留的洞见

剪枝后，报告将是唯一在活跃上下文中保留这些策略价值的载体。
（策略详情会同时存入知识库向量数据库，但不再参与后续决策）

## 研究背景资料
{research_context}

## 已有报告 (如有)
{existing_report}

## 任务
根据 Architect 的指令，综合当前所有策略的发现，生成阶段性研究报告。

报告应该：
1. 使用与原始问题相同的语言
2. 结构清晰，包含问题摘要、主要发现、对比分析、推荐方案等
3. **完整保留被剪枝策略的核心价值**
4. 如有外部搜索结果，正确引用来源
5. 如果已有报告，可以在其基础上增量更新

## 输出格式 (严格 JSON)
{{
    "report": "完整的 Markdown 格式报告",
    "report_summary": "一句话摘要",
    "key_findings": ["关键发现1", "关键发现2"],
    "branch_rationale": "解释为什么选择综合这些策略方向（用于知识库归档）"
}}
"""


def execute_synthesis_task(
    problem: str,
    strategies: List[StrategyNode],
    decision: Dict[str, Any],
    research_context: Optional[str],
    existing_report: Optional[str],
    report_version: int,
    api_key: str,
    use_mock: bool = False
) -> Dict[str, Any]:
    """
    Execute a synthesis/report task (when strategy_id is null).
    
    After synthesis, the strategies will be HARD PRUNED.
    Their value is preserved in:
    1. The report itself
    2. Knowledge base vector database (via write_strategy_archive)
    
    Args:
        problem: Original problem statement
        strategies: All strategies to synthesize (will be pruned after)
        decision: Architect's decision containing executor_instruction
        research_context: Research background if available
        existing_report: Existing report for incremental update
        report_version: Current report version number
        api_key: API key for LLM
        use_mock: Whether to run in mock mode
        
    Returns:
        Synthesis result containing report and prune_strategy_ids
    """
    # Get active strategies that will be synthesized (and pruned)
    active_strategies = [s for s in strategies if s.get("status") == "active"]
    prune_ids = [s["id"] for s in active_strategies]
    
    if use_mock:
        return {
            "report": f"# Mock 阶段性报告 v{report_version + 1}\n\n问题: {problem[:100]}...\n\n## 主要发现\n- Mock finding 1\n- Mock finding 2\n\n## 被综合策略\n{len(active_strategies)} 条策略已综合\n\n## 推荐方案\nMock recommendation.",
            "report_summary": "Mock synthesis completed",
            "key_findings": ["Mock finding 1", "Mock finding 2"],
            "branch_rationale": "Mock branch rationale for pruning decision",
            "prune_strategy_ids": prune_ids
        }
    
    # Format detailed strategies for pruning notification
    sorted_strategies = sorted(active_strategies, key=lambda s: s.get("score", 0), reverse=True)
    strategies_to_prune_list = []
    for i, s in enumerate(sorted_strategies):
        trajectory = s.get("trajectory", [])
        trajectory_summary = "\n".join([f"    - {t[:80]}..." for t in trajectory[-3:]]) if trajectory else "    (无执行记录)"
        strategies_to_prune_list.append(
            f"### {i+1}. {s.get('name', 'Unknown')} (Score: {s.get('score', 0):.3f})\n"
            f"- **理由**: {s.get('rationale', '')[:150]}...\n"
            f"- **假设**: {s.get('assumption', '')[:100]}...\n"
            f"- **执行轨迹**:\n{trajectory_summary}"
        )
    
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
    
    prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
        problem=problem,
        executor_instruction=decision.get("executor_instruction", "综合当前发现生成报告"),
        strategies_to_prune="\n\n".join(strategies_to_prune_list) or "无待剪枝策略",
        research_context=research_context[:2000] if research_context else "无研究背景",
        existing_report=existing_report[:1500] if existing_report else "无已有报告"
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
                "report": response.text,
                "report_summary": "Report generated",
                "key_findings": [],
                "branch_rationale": "Report generated (parse fallback)"
            }
        
        # Add prune IDs to result
        result["prune_strategy_ids"] = prune_ids
        return result
        
    except Exception as e:
        print(f"[Executor] Error executing synthesis task: {e}")
        return {
            "report": f"Error generating report: {str(e)}",
            "report_summary": "Error",
            "key_findings": [],
            "prune_strategy_ids": []  # Don't prune on error
        }


def executor_node(state: DeepThinkState) -> DeepThinkState:
    """
    Executor Node - 策略执行器
    
    基于 Architect 的决策，执行相应任务。
    - 当 strategy_id 存在时：对特定策略执行任务
    - 当 strategy_id 为 null 时：执行综合任务（如生成报告）
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
    synthesis_count = 0
    updated_report = state.get("final_report")
    report_version = state.get("report_version", 0)
    
    for decision in architect_decisions:
        strategy_id = decision.get("strategy_id")
        
        # Check if this is a synthesis task (strategy_id is null or special marker)
        is_synthesis = strategy_id is None or strategy_id == "null" or strategy_id == "SYNTHESIS"
        
        if is_synthesis:
            # Execute synthesis/report task
            print("  > Executing synthesis task...")
            
            result = execute_synthesis_task(
                problem=problem,
                strategies=strategies,
                decision=decision,
                research_context=state.get("research_context"),
                existing_report=updated_report,
                report_version=report_version,
                api_key=api_key,
                use_mock=use_mock
            )
            
            # Update report
            if result.get("report"):
                updated_report = result["report"]
                report_version += 1
                print(f"    Report updated (v{report_version})")
            
            # Execute hard pruning for synthesized strategies
            prune_ids = result.get("prune_strategy_ids", [])
            branch_rationale = result.get("branch_rationale", "")
            pruned_count = 0
            
            for sid in prune_ids:
                if sid in strategy_map:
                    s = strategy_map[sid]
                    
                    # Archive to knowledge base before pruning
                    try:
                        write_strategy_archive(
                            strategy=s,
                            synthesis_context=f"在报告 v{report_version} 中被综合",
                            branch_rationale=branch_rationale,
                            report_version=report_version
                        )
                    except Exception as e:
                        print(f"    [KB] Warning: Failed to archive {s.get('name')}: {e}")
                    
                    # Hard prune: mark as pruned_synthesized
                    s["status"] = "pruned_synthesized"
                    s["pruned_at_report_version"] = report_version
                    pruned_count += 1
            
            if pruned_count > 0:
                print(f"    Hard pruned {pruned_count} strategies, archived to KB")
            
            synthesis_count += 1
            
        elif strategy_id in strategy_map:
            # Execute strategy-specific task
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
                    "ucb_score": None,
                    "child_quota": 0,
                    "status": "active",
                    "trajectory": [f"[Executor] Generated as variant of {strategy['name']}"],
                    "parent_id": strategy["id"],
                    "pruned_at_report_version": None,
                    # 完整响应和思维摘要 - 确保前端能显示完整内容
                    "full_response": result.get("execution_result", ""),
                    "thinking_summary": f"由策略 '{strategy['name']}' 分支生成。\n洞见: {', '.join(result.get('new_insights', []))}"
                }
                new_strategies.append(new_node)
                print(f"    Created variant: '{new_node['name']}'")
            
            executed_count += 1
    
    # Merge new strategies with existing
    all_strategies = strategies + new_strategies
    
    print(f"[Executor] Executed {executed_count} strategy tasks, {synthesis_count} synthesis tasks, {len(new_strategies)} variants.")
    
    return {
        **state,
        "strategies": all_strategies,
        "architect_decisions": [],  # Clear decisions after execution
        "final_report": updated_report,
        "report_version": report_version,
        "history": state.get("history", []) + [
            f"Executor: {executed_count} tasks, {synthesis_count} synthesis, {len(new_strategies)} variants"
        ]
    }
