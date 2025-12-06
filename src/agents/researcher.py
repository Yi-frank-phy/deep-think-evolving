
import os
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.state import DeepThinkState

def research_node(state: DeepThinkState) -> DeepThinkState:
    """
    Provides research context for the problem.
    Note: Google Search Grounding is disabled for compatibility with thinking models.
    Uses the model's knowledge base instead.
    """
    print("\n[Researcher] Starting research analysis...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[Researcher] Error: GEMINI_API_KEY not set. Skipping research.")
        return state

    problem = state["problem_state"]
    
    # Configure GenAI
    genai.configure(api_key=api_key)
    
    # Use standard GenerativeModel WITHOUT tools for compatibility with thinking models
    model_name = os.environ.get("GEMINI_MODEL_RESEARCHER", os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
    print(f"[Researcher] Using model: {model_name}")
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    Please provide relevant background knowledge for the following problem:
    
    Topic: {problem}
    
    Focus on:
    1. Key concepts and definitions.
    2. Known approaches or state-of-the-art methods.
    3. Potential challenges or conflicting viewpoints.
    
    Provide a comprehensive summary based on your knowledge.
    """
    
    try:
        response = model.generate_content(prompt)
        research_context = response.text
        
        print(f"[Researcher] Research complete. Length: {len(research_context)} chars.")
        
        return {
            **state,
            "research_context": research_context,
            "history": state.get("history", []) + ["Researcher gathered context"]
        }
        
    except Exception as e:
        print(f"[Researcher] Error during research: {e}")
        return state
