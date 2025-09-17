from __future__ import annotations

import json
import os
from typing import Iterable, List, TypedDict

import google.generativeai as genai


class StrategyBlueprint(TypedDict):
    """Typed representation of a single strategy blueprint item."""

    strategy_name: str
    rationale: str
    initial_assumption: str


def _clean_response_text(raw_text: str) -> str:
    """Remove Markdown code fences and surrounding whitespace."""

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "", 1)
        cleaned = cleaned.replace("```", "")
    return cleaned.strip()


def _is_valid_strategy(candidate: object) -> bool:
    """Return True when the candidate satisfies the required schema."""

    if not isinstance(candidate, dict):
        return False

    required_keys = ("strategy_name", "rationale", "initial_assumption")
    for key in required_keys:
        value = candidate.get(key)
        if not isinstance(value, str) or not value.strip():
            return False
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

        valid_items.append(
            StrategyBlueprint(
                strategy_name=strategy["strategy_name"].strip(),
                rationale=strategy["rationale"].strip(),
                initial_assumption=strategy["initial_assumption"].strip(),
            )
        )

    return valid_items


def generate_strategic_blueprint(
    problem_state: str, model_name: str = "gemini-2.5-flash"
) -> list[StrategyBlueprint]:
    """Generate a list of strategic blueprints for the given problem state."""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please set the environment variable before running.")
        return []

    genai.configure(api_key=api_key)

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

请将结果输出为单一的JSON对象数组。每个对象必须包含以下三个键:
* strategy_name: 一个简短的、描述性的中文标签 (例如, "几何构造法").
* rationale: 一句解释该策略核心逻辑的中文描述。
* initial_assumption: 一句描述该策略若要可行所必须依赖的关键假设的中文描述。
"""

    full_user_prompt = user_prompt_template.format(problem_state=problem_state)

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )

    try:
        response = model.generate_content(
            full_user_prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            ),
        )
    except Exception as error:  # pragma: no cover - network errors
        print(f"An error occurred during API call: {error}")
        return []

    response_text = _clean_response_text(response.text)
    try:
        parsed_json = json.loads(response_text)
    except json.JSONDecodeError as error:
        print(f"Failed to parse JSON response from Gemini: {error}")
        return []

    if not isinstance(parsed_json, list):
        print(
            "Model response was not a JSON array; received "
            f"{type(parsed_json).__name__} instead."
        )
        return []

    validated = _validate_strategies(parsed_json)
    if not validated:
        print("No valid strategies were produced by the model.")
    return validated


if __name__ == "__main__":
    print("Running a direct test of strategy_architect.py...")

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
            print("\nSuccessfully generated strategic blueprint:")
            print(json.dumps(strategies, indent=2, ensure_ascii=False))
        else:
            print("\nFailed to generate strategic blueprint.")
