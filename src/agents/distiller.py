
import os
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.state import DeepThinkState

def distiller_node(state: DeepThinkState) -> DeepThinkState:
    """
    Distills the raw research context into a concise, actionable summary
    and injects it into the problem state.
    """
    print("\n[Distiller] Distilling research context...")
    
    context = state.get("research_context")
    if not context:
        print("[Distiller] No research context found. Skipping distillation.")
        return state
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return state

    model_name = os.environ.get("GEMINI_MODEL_DISTILLER", os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
    print(f"[Distiller] Using model: {model_name}")
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.2,
    )
    
    prompt = PromptTemplate(
        template="""\
你是一位 "信息提取专家" (Information Distiller)。
你的任务是从以下原始搜索结果中提取最关键的信息，去除噪音，并生成一断简练的 "背景摘要"。
这段摘要将被用于辅助 "战略架构师" 更好地理解问题背景并制定方案。

原始问题: {problem}

搜索结果:
{context}

请生成一段不超过 500 字的中文摘要，重点包含:
1. 核心定义与关键事实。
2. 现有解决方案的优缺点。
3. 任何可能影响战略制定的约束或机会。

摘要:
""",
        input_variables=["problem", "context"]
    )
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        summary = chain.invoke({
            "problem": state["problem_state"],
            "context": context
        })
        
        print(f"[Distiller] Distilled summary length: {len(summary)} chars.")
        
        # Inject into problem state
        new_problem_state = f"{state['problem_state']}\n\n[背景补充]:\n{summary}"
        
        return {
            **state,
            "problem_state": new_problem_state,
            "research_context": summary, # Optional: replace raw with summary or keep raw? Let's keep summary.
            "history": state.get("history", []) + ["Distiller refined context"]
        }
        
    except Exception as e:
        print(f"[Distiller] Error: {e}")
        return state
