
import os
from google import genai
from google.genai import types
from src.core.state import DeepThinkState

def research_node(state: DeepThinkState) -> DeepThinkState:
    """
    Performs Google Search Grounding to gather context for the problem.
    Uses the new google-genai SDK with Tool(google_search=GoogleSearch()).
    """
    print("\n[Researcher] Starting Google Search Grounding...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[Researcher] Error: GEMINI_API_KEY not set. Skipping research.")
        return state

    problem = state["problem_state"]
    
    # Initialize client with API key
    client = genai.Client(api_key=api_key)
    
    # Configure grounding tool
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    
    # Get model name from env
    model_name = os.environ.get("GEMINI_MODEL_RESEARCHER", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite"))
    print(f"[Researcher] Using model: {model_name}")
    
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )
    
    prompt = f"""
    Please research the following topic to provide a comprehensive background for solving it:
    
    Topic: {problem}
    
    Focus on:
    1. Key concepts and definitions.
    2. Recent developments or state-of-the-art approaches.
    3. Potential challenges or conflicting viewpoints.
    
    Provide a detailed summary with citations if possible.
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        research_context = response.text
        
        print(f"[Researcher] Research complete. Length: {len(research_context)} chars.")
        
        return {
            **state,
            "research_context": research_context,
            "history": state.get("history", []) + ["Researcher gathered context via Google Search"]
        }
        
    except Exception as e:
        print(f"[Researcher] Error during search: {e}")
        return state
