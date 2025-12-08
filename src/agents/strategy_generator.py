"""
StrategyGenerator Agent - 策略生成器

仅负责基于充足的研究上下文生成所有可能的策略。
从原 Architect 中分离出来，职责单一化。
"""

import os
import uuid
from typing import List

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.state import DeepThinkState, StrategyNode


STRATEGY_GENERATOR_PROMPT = """\
你是一位"战略系统架构师" (Strategic Systems Architect)。
你的主要职能是对复杂问题进行元层面分析。
你不直接解决问题，而是识别并绘制出所有通往解决方案的基础战略路径。
你的分析必须广博、多样，并专注于概念上截然不同的方法。

## 问题背景
{problem_state}

## 研究资料
{research_context}

## 子任务分解
{subtasks}

## 任务
生成一份详尽的、包含所有从此状态出发的、相互排斥的战略方向清单。
对每一个方向，请提供一个简洁的名称、清晰的理由和其所依赖的核心假设。

## 约束
1. **最大化多样性**: 策略之间必须存在根本性差异。避免对同一核心思想的微小改动。
2. **仅限高层次**: 不要提供详细的程序步骤。专注于"做什么"和"为什么"，而不是"怎么做"。
3. **保持中立**: 不要对策略表示任何偏好或进行评估。你的角色是绘制蓝图，而非评判。

## 输出格式 (严格 JSON 数组)
[
    {{
        "strategy_name": "简短的描述性名称",
        "rationale": "解释该策略核心逻辑的描述",
        "initial_assumption": "该策略若要可行所必须依赖的关键假设",
        "milestones": [
            {{"title": "阶段名", "summary": "简要说明"}}
        ]
    }}
]
"""


def strategy_generator_node(state: DeepThinkState) -> DeepThinkState:
    """
    Strategy Generator Node - 策略生成器
    
    基于研究上下文生成所有可能的初始策略。
    仅负责生成，不负责评分或调度。
    """
    print("\n[StrategyGenerator] Generating strategic blueprints...")
    
    problem_state = state["problem_state"]
    research_context = state.get("research_context", "无额外研究资料")
    subtasks = state.get("subtasks", [])
    
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true" or not api_key
    
    if use_mock:
        print("[StrategyGenerator] Running in MOCK MODE.")
        raw_strategies = [
            {
                "strategy_name": "策略 A: 直接方法",
                "rationale": "采用最直接的解决路径",
                "initial_assumption": "资源充足，无重大障碍",
                "milestones": [{"title": "分析", "summary": "问题分析"}]
            },
            {
                "strategy_name": "策略 B: 分治方法",
                "rationale": "将问题分解为独立子问题",
                "initial_assumption": "子问题间相互独立",
                "milestones": [{"title": "分解", "summary": "问题分解"}]
            },
            {
                "strategy_name": "策略 C: 类比方法",
                "rationale": "借鉴相似领域的成功经验",
                "initial_assumption": "存在可迁移的先例",
                "milestones": [{"title": "调研", "summary": "先例调研"}]
            }
        ]
    else:
        model_name = os.environ.get(
            "GEMINI_MODEL_GENERATOR",
            os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        )
        print(f"[StrategyGenerator] Using model: {model_name}")
        
        config = state.get("config", {})
        thinking_budget = config.get("thinking_budget", 1024)
        
        generation_config = {}
        if thinking_budget > 0:
            generation_config["thinking_config"] = {
                "include_thoughts": True,
                "thinking_budget": thinking_budget
            }
        
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            generation_config=generation_config
        )
        
        parser = JsonOutputParser()
        prompt = PromptTemplate(
            template=STRATEGY_GENERATOR_PROMPT,
            input_variables=["problem_state", "research_context", "subtasks"]
        )
        
        chain = prompt | llm | parser
        
        subtasks_str = "\n".join([f"- {s}" for s in subtasks]) if subtasks else "无子任务分解"
        
        try:
            response = chain.invoke({
                "problem_state": problem_state,
                "research_context": research_context,
                "subtasks": subtasks_str
            })
            
            if isinstance(response, dict):
                raw_strategies = [response]
            elif isinstance(response, list):
                raw_strategies = response
            else:
                raw_strategies = []
                
        except Exception as e:
            print(f"[StrategyGenerator] Error: {e}")
            raw_strategies = []
    
    # Convert to StrategyNode format
    new_strategies: List[StrategyNode] = []
    for raw in raw_strategies:
        if not isinstance(raw, dict):
            continue
        if not raw.get("strategy_name") or not raw.get("rationale"):
            continue
            
        node: StrategyNode = {
            "id": str(uuid.uuid4()),
            "name": raw.get("strategy_name", "Unnamed Strategy"),
            "rationale": raw.get("rationale", ""),
            "assumption": raw.get("initial_assumption", ""),
            "milestones": raw.get("milestones", []),
            
            # Initialize metrics (to be computed in Evolution)
            "embedding": None,
            "density": None,
            "log_density": None,
            "score": 0.0,
            
            "status": "active",
            "trajectory": ["[StrategyGenerator] Initial generation"],
            "parent_id": None
        }
        new_strategies.append(node)
    
    print(f"[StrategyGenerator] Generated {len(new_strategies)} strategies.")
    
    return {
        **state,
        "strategies": new_strategies,
        "history": state.get("history", []) + [
            f"StrategyGenerator: {len(new_strategies)} strategies generated"
        ]
    }
