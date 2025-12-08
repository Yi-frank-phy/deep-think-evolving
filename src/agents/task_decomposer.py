"""
TaskDecomposer Agent - 任务拆解专家

负责将复杂问题分解为可处理的子任务，并列出信息需求清单。
这是进化循环的第一个 Agent，为后续的 Researcher 提供搜索方向。
"""

import os
from typing import List, TypedDict

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.state import DeepThinkState


class InformationNeed(TypedDict):
    """Single information need with priority."""
    topic: str
    type: str  # "factual" | "procedural" | "conceptual"
    priority: int  # 1-5


class DecompositionResult(TypedDict):
    """Result of task decomposition."""
    subtasks: List[str]
    information_needs: List[InformationNeed]


TASK_DECOMPOSER_PROMPT = """\
你是一位"任务拆解专家"，负责：
1. 将复杂问题分解为可处理的子任务
2. 分析每个子任务需要哪些领域知识
3. 生成"信息需求清单"，指导后续搜索

## 输入问题
{problem}

## 任务
请分析上述问题，输出：
1. 子任务列表：将问题拆解为若干独立可处理的子问题
2. 信息需求清单：列出解决这些子问题需要的外部知识

## 输出格式 (严格 JSON)
{{
    "subtasks": [
        "子任务1描述",
        "子任务2描述",
        ...
    ],
    "information_needs": [
        {{
            "topic": "需要搜索的主题",
            "type": "factual|procedural|conceptual",
            "priority": 1-5
        }},
        ...
    ]
}}

注意：
- subtasks 应该是相互独立、可并行处理的子问题
- information_needs 的 type 说明:
  - factual: 事实性知识（定义、数据、现状）
  - procedural: 程序性知识（方法、步骤、最佳实践）
  - conceptual: 概念性知识（原理、理论、关系）
- priority 1-5: 5 表示最重要
"""


def task_decomposer_node(state: DeepThinkState) -> DeepThinkState:
    """
    Task Decomposer Node - 任务拆解专家
    
    将复杂问题分解为子任务和信息需求清单。
    这是进化流程的入口点，为 Researcher 提供搜索方向。
    """
    print("\n[TaskDecomposer] Decomposing problem into subtasks...")
    
    problem = state["problem_state"]
    
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key
    
    if use_mock:
        print("[TaskDecomposer] Running in MOCK MODE.")
        decomposition = {
            "subtasks": [
                "分析问题的核心约束条件",
                "识别可能的解决方案类别",
                "评估各方案的可行性"
            ],
            "information_needs": [
                {"topic": "相关领域的现有解决方案", "type": "factual", "priority": 5},
                {"topic": "问题领域的基本原理", "type": "conceptual", "priority": 4},
                {"topic": "实施方法和最佳实践", "type": "procedural", "priority": 3}
            ]
        }
    else:
        model_name = os.environ.get(
            "GEMINI_MODEL_DECOMPOSER",
            os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        )
        print(f"[TaskDecomposer] Using model: {model_name}")
        
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.3,  # Low temperature for structured decomposition
        )
        
        parser = JsonOutputParser()
        prompt = PromptTemplate(
            template=TASK_DECOMPOSER_PROMPT,
            input_variables=["problem"]
        )
        
        chain = prompt | llm | parser
        
        try:
            decomposition = chain.invoke({"problem": problem})
        except Exception as e:
            print(f"[TaskDecomposer] Error: {e}")
            decomposition = {
                "subtasks": ["分析完整问题"],
                "information_needs": [
                    {"topic": problem[:100], "type": "factual", "priority": 5}
                ]
            }
    
    subtask_count = len(decomposition.get("subtasks", []))
    info_needs_count = len(decomposition.get("information_needs", []))
    
    print(f"[TaskDecomposer] Decomposed into {subtask_count} subtasks, {info_needs_count} information needs.")
    
    return {
        **state,
        "subtasks": decomposition.get("subtasks", []),
        "information_needs": decomposition.get("information_needs", []),
        "history": state.get("history", []) + [
            f"TaskDecomposer: {subtask_count} subtasks, {info_needs_count} info needs"
        ]
    }
