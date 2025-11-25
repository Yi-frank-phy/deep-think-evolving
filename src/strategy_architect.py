import os
import json
from typing import Any

import google.generativeai as genai


def generate_strategic_blueprint(
    problem_state: str, model_name: str = "gemini-2.5-flash"
) -> list[dict[str, Any]]:
    """
    Generates a strategic blueprint for a given problem state using a generative AI model.

    This function takes a description of a problem and uses the "Strategy Architect"
    prompt pattern defined in the project's design document to generate a list of
    potential strategic directions.

    Args:
        problem_state: A string describing the current problem, context, progress,
            and any specific dilemmas.
        model_name: The Gemini model name to use for generation.

    Returns:
        A list of dictionaries, where each dictionary represents a strategy and
        contains the keys 'strategy_name', 'rationale', 'initial_assumption',
        and 'milestones'. The `milestones` field is a nested mapping of
        high-level phases to milestone arrays. Each milestone entry must include
        a `title`, a descriptive `summary`, and a list of `success_criteria`
        strings that make the checkpoint verifiable. Returns an empty list if
        the API key is not configured or an error occurs.
    """
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

请将结果输出为单一的JSON对象数组。每个对象必须包含以下字段:
* strategy_name: 一个简短的、描述性的中文标签 (例如, "几何构造法")。
* rationale: 一句解释该策略核心逻辑的中文描述。
* initial_assumption: 一句描述该策略若要可行所必须依赖的关键假设的中文描述。
* milestones: 一个JSON对象, 其键为阶段名称 (如 "阶段 1: 发现"), 值为该阶段的里程碑数组。
  - 里程碑对象必须包含 title (名称)、summary (简要说明) 以及 success_criteria
    (字符串数组, 描述达成该里程碑需满足的可验证标准)。
  - 若某阶段没有额外需求, 仍需提供至少一个里程碑来解释该阶段的目标。
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

        response_text = getattr(response, "text", "").strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(response_text)

        if isinstance(parsed_json, dict):
            parsed_json = [parsed_json]

        if not isinstance(parsed_json, list):
            return []

        normalized: list[dict] = []
        for entry in parsed_json:
            if not isinstance(entry, dict):
                continue

            milestones = entry.get("milestones", [])
            if isinstance(milestones, dict):
                milestones = [milestones]
            elif not isinstance(milestones, list):
                milestones = [milestones] if milestones else []

            normalized.append({**entry, "milestones": milestones})

        return normalized

    except Exception as e:
        print(f"An error occurred during API call or JSON parsing: {e}")
        return []


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
