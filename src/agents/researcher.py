
import os
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.state import DeepThinkState

def research_node(state: DeepThinkState) -> DeepThinkState:
    """
    Performs Google Search Grounding to gather context for the problem.
    """
    print("\n[Researcher] Starting Google Search Grounding...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[Researcher] Error: GEMINI_API_KEY not set. Skipping research.")
        return state

    problem = state["problem_state"]
    
    # Configure GenAI directly for Search Grounding
    genai.configure(api_key=api_key)
    
    # Using the 'tools' parameter in Model 
    # Reference: https://ai.google.dev/gemini-api/docs/grounding?lang=python
    
    model = genai.GenerativeModel(
        'models/gemini-1.5-flash-latest',
        tools='google_search_retrieval'
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
        response = model.generate_content(prompt)
        research_context = response.text
        
        # Accessing grounding metadata if needed (not supported in simple text extraction)
        # grounding_metadata = response.candidates[0].grounding_metadata
        
        print(f"[Researcher] Research complete. Length: {len(research_context)} chars.")
        
        return {
            **state,
            "research_context": research_context,
            "history": state.get("history", []) + ["Researcher gathered context"]
        }
        
    except Exception as e:
        print(f"[Researcher] Error during search: {e}")
        return state
