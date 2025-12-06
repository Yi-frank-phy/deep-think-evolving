from __future__ import annotations

import os
from typing import Any, Iterable, List, TypedDict, Union

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

import os
DEFAULT_MODEL_NAME = os.environ.get("GEMINI_MODEL_ARCHITECT", os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))


class StrategyBlueprint(TypedDict):
    """Typed representation of a single strategy blueprint item."""

    strategy_name: str
    rationale: str
    initial_assumption: str
    milestones: Union[dict[str, Any], list[Any]]


def _is_valid_strategy(candidate: object) -> bool:
    """Return True when the candidate satisfies the required schema."""

    if not isinstance(candidate, dict):
        return False

    required_keys = ("strategy_name", "rationale", "initial_assumption")
    for key in required_keys:
        value = candidate.get(key)
        if not isinstance(value, str) or not value.strip():
            return False
            
    # Milestones are optional in strict validation but should be present in final output
    return True


def _validate_strategies(strategies: Iterable[dict]) -> List[StrategyBlueprint]:
    """Validate and normalise the generated strategies."""

    valid_items: List[StrategyBlueprint] = []
    for index, strategy in enumerate(strategies, start=1):
        if not _is_valid_strategy(strategy):
            print(
                "Warning: Ignoring malformed strategy at position "
                f"{index}: {strategy!r}"
            )
            continue

        milestones = strategy.get("milestones", {})
        # Normalize milestones: ensure it's a dict or list, default to dict
        if not isinstance(milestones, (dict, list)):
            milestones = {}

        valid_items.append(
            StrategyBlueprint(
                strategy_name=strategy["strategy_name"].strip(),
                rationale=strategy["rationale"].strip(),
                initial_assumption=strategy["initial_assumption"].strip(),
                milestones=milestones,
            )
        )

    return valid_items


def generate_strategic_blueprint(
    problem_state: str, model_name: str = DEFAULT_MODEL_NAME, thinking_budget: int = 1024
) -> list[StrategyBlueprint]:
    """
    Generates a strategic blueprint for a given problem state using LangChain and Gemini.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please set the environment variable before running.")
        return []

    # Initialize the ChatGoogleGenerativeAI model
    # Note: 'thinking_v2' is a hypothetical config for Gemini 2.5. 
    # If the library doesn't support 'thinking_config', this might need adjustment.
    # We pass it as a kwarg hoping the underlying client picks it up, or use generation_config.
    
    generation_config = {}
    if thinking_budget > 0:
        # Based on docs: thinking_config with snake_case keys for Python SDK
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

    system_prompt = (
        "你是一位'战略系统架构师' (Strategic Systems Architect)。"
        "你的主要职能是对复杂问题进行元层面分析。"
        "你不直接解决问题，而是识别并绘制出所有通往解决方案的基础战略路径。"
        "你的分析必须广博、多样，并专注于概念上截然不同的方法。"
    )

    user_prompt_template = """\
分析以下问题状态：
{problem_state}

你的任务是生成一份详尽的、包含所有从此状态出发的、相互排斥的战略方向清单。对每一个方向，请提供一个简洁的名称、清晰的理由和其所依赖的核心假设。
约束:
1. ## 最大化多样性: 策略之间必须存在根本性差异。避免对同一核心思想的微小改动。
2. 仅限高层次: 不要提供详细的程序步骤。专注于“做什么”和“为什么”，而不是“怎么做”。
3. 保持中立: 不要对策略表示任何偏好或进行评估。你的角色是绘制蓝图，而非评判。

请将结果输出为单一的JSON对象数组。每个对象必须包含以下字段:
* strategy_name: 一个简短的、描述性的中文标签 (例如, "几何构造法")。
* rationale: 一句解释该策略核心逻辑的中文描述。
* initial_assumption: 一句描述该策略若要可行所必须依赖的关键假设的中文描述。
* milestones: 一个JSON对象, 其键为阶段名称 (如 "阶段 1: 发现"), 值为该阶段的里程碑数组。
  - 里程碑对象必须包含 title (名称)、summary (简要说明) 以及 success_criteria
    (字符串数组, 描述达成该里程碑需满足的可验证标准)。
  - 若某阶段没有额外需求, 仍需提供至少一个里程碑来解释该阶段的目标。
"""

    parser = JsonOutputParser()
    
    prompt = PromptTemplate(
        template=f"{system_prompt}\n\n{user_prompt_template}\n\n{{format_instructions}}",
        input_variables=["problem_state"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser

    try:
        response = chain.invoke({"problem_state": problem_state})
    except Exception as error:
        print(f"An error occurred during LangChain execution: {error}")
        return []

    if isinstance(response, dict):
        response = [response]

    if not isinstance(response, list):
        print(
            "Model response was not a JSON array; received "
            f"{type(response).__name__} instead."
        )
        return []

    validated = _validate_strategies(response)
    if not validated:
        print("No valid strategies were produced by the model.")
    return validated


if __name__ == "__main__":
    print("Running a direct test of strategy_architect.py (LangChain)...")

    if not os.environ.get("GEMINI_API_KEY"):
        print("\nSkipping test: GEMINI_API_KEY is not set.")
        print("Please export your API key to run the test:")
        print("export GEMINI_API_KEY='your_api_key_here'")
    else:
        sample_problem = (
            "我们正在开发一个大型语言模型驱动的自主研究代理。"
            "当前进展：代理可以分解问题、执行网络搜索并阅读文档。"
            "遇到的困境：当面对需要综合来自多个来源的矛盾信息才能得出结论的复杂问题时，"
            "代理的性能会急剧下降。它经常会陷入其中一个信源的观点，或者无法形成一个连贯的最终答案。"
        )

        strategies = generate_strategic_blueprint(sample_problem)

        if strategies:
            import json
            print("\nSuccessfully generated strategic blueprint:")
            print(json.dumps(strategies, indent=2, ensure_ascii=False))
        else:
            print("\nFailed to generate strategic blueprint.")
