"""
Researcher Agent - 深度研究专家

基于信息需求清单进行搜索，并在单次调用中自我反思信息充足性。
成本优化设计：不使用 ReAct 多轮循环，而是让 Agent 在单次调用中完成反思。
所有 Agent 都有 Grounding 能力，这不是 Researcher 的特权。
"""

import os
import json
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types
from src.core.state import DeepThinkState


RESEARCHER_PROMPT_TEMPLATE = """\
你是一位"深度研究专家"，拥有 Google Search Grounding 工具能力。

## 任务
基于以下信息需求清单，搜集足够的背景资料以支撑后续策略生成。

## 原始问题
{problem}

## 信息需求清单
{information_needs}

## 工作流程
1. 针对每个需求调用 grounding 获取信息
2. 【自我反思】评估当前收集的信息是否充足：
   - 若充足：输出汇总的 research_context
   - 若不足：在输出中标注缺失项（供下一轮补充）

## 输出格式 (严格 JSON)
{{
    "research_context": "汇总的研究背景（详细、结构化）",
    "information_status": "sufficient" 或 "insufficient",
    "missing_items": ["缺失项1", "缺失项2"]  // 仅当 insufficient 时填写，否则为空数组
}}

注意：
- research_context 应该是详细、结构化的研究摘要，包含所有收集到的信息
- 如果信息充足，missing_items 应该是空数组 []
- 请务必输出有效的 JSON 格式
"""


def research_node(state: DeepThinkState) -> DeepThinkState:
    """
    Researcher Node - 深度研究专家
    
    基于信息需求清单进行 Google Search Grounding，并在单次调用中自我反思信息充足性。
    成本优化：不使用 ReAct 多轮循环，而是让 Agent 自行评估并反思。
    """
    print("\n[Researcher] Starting information-needs-driven research...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true"
    
    if not api_key and not use_mock:
        print("[Researcher] Error: GEMINI_API_KEY not set. Returning sufficient to proceed.")
        return {
            **state,
            "research_context": "No API key available - proceeding without research.",
            "research_status": "sufficient",  # Avoid infinite loop
            "research_iteration": state.get("research_iteration", 0) + 1
        }

    problem = state["problem_state"]
    information_needs = state.get("information_needs", [])
    
    # Check iteration limit
    config = state.get("config", {})
    max_iterations = config.get("max_research_iterations", 3)
    current_iteration = state.get("research_iteration", 0)
    
    if current_iteration >= max_iterations:
        print(f"[Researcher] Max iterations ({max_iterations}) reached. Proceeding with available context.")
        return {
            **state,
            "research_status": "sufficient",  # Force sufficient to proceed
            "history": state.get("history", []) + [
                f"Researcher: max iterations reached, proceeding with available context"
            ]
        }
    
    # Format information needs for prompt
    if information_needs:
        info_needs_str = "\n".join([
            f"- [{need.get('priority', 3)}/5] {need.get('topic', '')} ({need.get('type', 'factual')})"
            for need in information_needs
        ])
    else:
        info_needs_str = f"- [5/5] {problem[:200]}... (自动生成的信息需求)"
    
    use_mock = os.environ.get("USE_MOCK_AGENTS", "false").lower() == "true"
    
    if use_mock:
        print("[Researcher] Running in MOCK MODE.")
        result = {
            "research_context": f"Mock research context for: {problem[:100]}...\n模拟的研究背景信息，包含相关定义、现有方法和潜在挑战。",
            "information_status": "sufficient",
            "missing_items": []
        }
    else:
        # Initialize client with API key
        client = genai.Client(api_key=api_key)
        
        # Configure grounding tool
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        
        # Get model name from env
        model_name = os.environ.get(
            "GEMINI_MODEL_RESEARCHER",
            os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        )
        print(f"[Researcher] Using model: {model_name}")
        print(f"[Researcher] Iteration: {current_iteration + 1}/{max_iterations}")
        
        grounding_config = types.GenerateContentConfig(
            tools=[grounding_tool],
            # Note: response_mime_type is NOT compatible with tools/grounding
        )
        
        prompt = RESEARCHER_PROMPT_TEMPLATE.format(
            problem=problem,
            information_needs=info_needs_str
        )
        
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=grounding_config,
            )
            
            # Parse JSON response
            try:
                result = json.loads(response.text)
            except json.JSONDecodeError:
                # Fallback: treat entire response as context
                result = {
                    "research_context": response.text,
                    "information_status": "sufficient",
                    "missing_items": []
                }
                
        except Exception as e:
            print(f"[Researcher] Error during search: {e}")
            result = {
                "research_context": state.get("research_context", ""),
                "information_status": "insufficient",
                "missing_items": ["搜索过程出错，需要重试"]
            }
    
    research_context = result.get("research_context") or ""  # Ensure not None
    information_status = result.get("information_status", "sufficient")
    missing_items = result.get("missing_items", [])
    
    print(f"[Researcher] Research complete. Status: {information_status}")
    print(f"[Researcher] Context length: {len(research_context) if research_context else 0} chars")
    
    if missing_items:
        print(f"[Researcher] Missing items: {missing_items}")
    
    return {
        **state,
        "research_context": research_context,
        "research_status": information_status,
        "research_iteration": current_iteration + 1,
        "history": state.get("history", []) + [
            f"Researcher: {len(research_context)} chars, status={information_status}"
        ]
    }

