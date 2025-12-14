"""
WriterAgent - 最终报告生成器

在进化过程收敛后，将所有研究发现综合成一份结构化的最终报告/回答。

参考设计: LangChain Open Deep Research 的 final_report_generation
"""

import os
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.state import DeepThinkState, StrategyNode


# System prompt for WriterAgent
WRITER_SYSTEM_PROMPT = """\
你是一位专业的研究报告撰写者 (Writer Agent)。你的任务是将进化研究过程的成果综合成一份清晰、结构化的最终报告。

## 你的职责

1. **综合分析**：整合所有收敛后的策略，提取核心洞见
2. **结构化输出**：生成易于阅读的报告，包含问题总结、主要发现、推荐方案
3. **引用来源**：如有搜索结果或外部信息，正确引用
4. **语言适配**：使用与用户问题相同的语言撰写报告

## 报告风格

- 使用 Markdown 格式
- 专业但易懂的语言
- 重点突出关键发现
- 提供可操作的建议
"""


REPORT_GENERATION_PROMPT = """\
基于以下进化研究过程的成果，生成一份全面、结构化的最终报告：

---

## 原始问题

{problem_state}

---

## 研究背景

{research_context}

---

## 策略分析结果（按评分从高到低）

{strategies_summary}

---

## 迭代统计

- 总迭代次数: {iteration_count}
- 最终空间熵: {final_entropy:.4f}
- 策略总数: {total_strategies}（活跃: {active_count}，已扩展: {expanded_count}）

---

## 报告生成任务

请生成一份详细的研究报告，包含以下部分：

### 1. 问题摘要
简洁重述问题核心，明确研究目标。

### 2. 主要发现
- 排名最高的策略及其核心思路
- 关键洞见和突破点
- 不同策略之间的共性和差异

### 3. 对比分析
分析各策略的优劣势，解释为何某些策略表现更好。

### 4. 推荐方案
基于分析结果，给出具体可操作的建议。

### 5. 来源引用（如有）
如果研究过程中使用了外部搜索结果，列出参考链接。

---

**语言要求**：请使用与"原始问题"相同的语言撰写整份报告。
"""


def _format_strategies_summary(strategies: List[StrategyNode], top_n: int = 5) -> str:
    """Format top strategies into a readable summary."""
    if not strategies:
        return "（无策略数据）"
    
    # Sort by score (descending)
    sorted_strategies = sorted(
        strategies,
        key=lambda s: s.get("score", 0),
        reverse=True
    )
    
    lines = []
    for i, s in enumerate(sorted_strategies[:top_n]):
        status = s.get("status", "unknown")
        score = s.get("score", 0)
        name = s.get("name", "未命名策略")
        rationale = s.get("rationale", "无描述")
        assumption = s.get("assumption", "无假设")
        
        # Get last few trajectory entries
        trajectory = s.get("trajectory", [])
        recent_trajectory = trajectory[-3:] if trajectory else []
        trajectory_str = "\n".join([f"      - {t}" for t in recent_trajectory]) if recent_trajectory else "      （无执行记录）"
        
        lines.append(f"""
### {i+1}. {name}
- **状态**: {status}
- **评分**: {score:.3f}
- **核心思路**: {rationale[:200]}...
- **关键假设**: {assumption[:150]}...
- **最近执行**:
{trajectory_str}
""")
    
    # Add summary of remaining strategies if any
    remaining = len(sorted_strategies) - top_n
    if remaining > 0:
        lines.append(f"\n*（另有 {remaining} 条策略未详细展示）*")
    
    return "\n".join(lines)


def writer_node(state: DeepThinkState) -> DeepThinkState:
    """
    WriterAgent: 将所有收敛的策略综合成最终报告。
    
    在 Evolution 判定收敛后调用，生成 final_report 字段。
    
    功能：
    1. 收集所有策略和研究上下文
    2. 调用 LLM 生成结构化报告
    3. 支持多语言（跟随用户问题语言）
    """
    print("\n[Writer] Generating final report...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key
    
    if not api_key and not use_mock:
        print("[Writer] Error: GEMINI_API_KEY not set. Generating placeholder report.")
        return {
            **state,
            "final_report": "⚠️ 无法生成报告：未配置 GEMINI_API_KEY",
            "history": state.get("history", []) + ["[Writer] 报告生成失败（无 API Key）"]
        }
    
    # Collect data from state
    problem_state = state.get("problem_state", "（无问题描述）")
    research_context = state.get("research_context") or "（无研究背景资料）"
    strategies = state.get("strategies", [])
    iteration_count = state.get("iteration_count", 0)
    spatial_entropy = state.get("spatial_entropy", 0.0)
    
    # Calculate strategy statistics
    active_count = len([s for s in strategies if s.get("status") == "active"])
    expanded_count = len([s for s in strategies if s.get("status") == "expanded"])
    total_strategies = len(strategies)
    
    # Format strategies summary
    strategies_summary = _format_strategies_summary(strategies, top_n=5)
    
    if use_mock:
        print("[Writer] Running in MOCK MODE.")
        # Generate mock report
        mock_report = f"""# 📝 研究报告 (Mock)

## 问题摘要
{problem_state[:200]}...

## 主要发现
- 共生成 {total_strategies} 条策略
- 经过 {iteration_count} 轮迭代收敛
- 最终空间熵: {spatial_entropy:.4f}

## 推荐方案
基于 Mock 模式，无法生成真实分析。请配置 GEMINI_API_KEY 获取完整报告。

---
*此报告由 Mock 模式生成*
"""
        print("[Writer] Mock report generated.")
        return {
            **state,
            "final_report": mock_report,
            "history": state.get("history", []) + ["[Writer] Mock 最终报告已生成"]
        }
    
    # Initialize LLM
    model_name = os.environ.get(
        "GEMINI_MODEL_WRITER",
        os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    )
    print(f"[Writer] Using model: {model_name}")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,  # Slightly creative for report writing
        )
        
        # Build prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", WRITER_SYSTEM_PROMPT),
            ("human", REPORT_GENERATION_PROMPT)
        ])
        
        messages = prompt.format_messages(
            problem_state=problem_state,
            research_context=research_context[:2000],  # Truncate if too long
            strategies_summary=strategies_summary,
            iteration_count=iteration_count,
            final_entropy=spatial_entropy,
            total_strategies=total_strategies,
            active_count=active_count,
            expanded_count=expanded_count
        )
        
        # Generate report
        response = llm.invoke(messages)
        final_report = response.content
        
        print(f"[Writer] Report generated ({len(final_report)} chars)")
        
        return {
            **state,
            "final_report": final_report,
            "history": state.get("history", []) + [
                f"[Writer] 最终报告已生成 ({len(final_report)} 字符)"
            ]
        }
        
    except Exception as e:
        error_msg = f"⚠️ 报告生成失败: {str(e)}"
        print(f"[Writer] Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            **state,
            "final_report": error_msg,
            "history": state.get("history", []) + [f"[Writer] 报告生成错误: {e}"]
        }
