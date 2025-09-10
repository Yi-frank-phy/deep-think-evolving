import os
import json
import google.generativeai as genai

def generate_strategic_blueprint(
    problem_state: str, model_name: str = "gemini-2.5-flash"
) -> list[dict]:
    """
    Generates a strategic blueprint for a given problem state using a generative AI model.

    This function takes a description of a problem and uses the "Strategy Architect"
    prompt pattern defined in the project's design document to generate a list of
    potential strategic directions.

    Args:
        problem_state: A string describing the current problem, context, progress,
                       and any specific dilemmas.
        model_name: The name of the generative model to use.

    Returns:
        A list of dictionaries, where each dictionary represents a strategy and
        contains the keys 'strategy_name', 'rationale', and 'initial_assumption'.
        Returns an empty list if the API key is not configured or an error occurs.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
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
* strategy_name: 一个简短的、描述性的中文标签 (例如, "几何构造法")。
* rationale: 一句解释该策略核心逻辑的中文描述。
* initial_assumption: 一句描述该策略若要可行所必须依赖的关键假设的中文描述。
"""

    full_user_prompt = user_prompt_template.format(problem_state=problem_state)

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt
    )

    try:
        response = model.generate_content(
            full_user_prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )

        # The response text should be a JSON formatted string.
        # It might be wrapped in ```json ... ```, so we need to clean it.
        response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(response_text)
        return parsed_json

    except Exception as e:
        print(f"An error occurred during API call or JSON parsing: {e}")
        return []
