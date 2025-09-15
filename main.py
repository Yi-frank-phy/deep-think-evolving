import os
import json
import numpy as np

from src.grounding_search import GroundingSearchError, search_google_grounding
from src.strategy_architect import generate_strategic_blueprint
from src.embedding_client import embed_strategies
from src.diversity_calculator import calculate_similarity_matrix


def main():
    """Run the end-to-end test pipeline for strategy generation and analysis."""
    print("--- Running Full Pipeline Test Script (Gemini + Ollama) ---")

    print("\n--- Grounding Search Demo (Google Search Grounding) ---")
    grounding_metadata_for_reference = None
    try:
        search_demo = search_google_grounding(
            "Gemini 1.5 Flash 最新能力更新", top_k=3
        )
    except GroundingSearchError as error:
        print("[GROUNDING ERROR] Could not run Google Search Grounding demo.")
        print(error)
        print(
            "Please ensure GEMINI_API_KEY is configured and that your network allows "
            "outbound access to Google APIs."
        )
    else:
        print("Grounding results:")
        print(json.dumps(search_demo["results"], indent=2, ensure_ascii=False))
        grounding_metadata_for_reference = search_demo.get("grounding_metadata")
        if isinstance(grounding_metadata_for_reference, dict):
            chunk_count = len(grounding_metadata_for_reference.get("grounding_chunks", []))
        else:
            chunk_count = 0
        print(
            "Stored raw grounding metadata for future use "
            f"({chunk_count} grounding chunks captured)."
        )

    # Ensure the Gemini API key is available before attempting generation.
    if not os.environ.get("GEMINI_API_KEY"):
        print("\n[ERROR] GEMINI_API_KEY environment variable is not set.")
        print("This script requires a Google Gemini API key for the generation step.")
        print("\nPlease set the environment variable before running:")
        print("  export GEMINI_API_KEY='your_google_api_key_here'")
        print("\nScript finished without execution.")
        return

    # 1. Generate Strategic Blueprints
    # ---------------------------------
    problem_state = (
        "我们正在开发一个大型语言模型驱动的自主研究代理。"
        "当前进展：代理可以分解问题、执行网络搜索并阅读文档。"
        "遇到的困境：当面对需要综合来自多个来源的矛盾信息才能得出结论的复杂问题时，"
        "代理的性能会急剧下降。它经常会陷入其中一个信源的观点，或者无法形成一个连贯的最终答案。"
    )
    print(f"\nProblem State:\n{problem_state}")
    print("\nStep 1: Generating strategic blueprint (using Gemini)...")

    # Per the model usage policy for testing, use the 'lite' version.
    # Note: Using gemini-1.5-flash as a stand-in for the hypothetical gemini-2.5-flash-lite
    strategies = generate_strategic_blueprint(
        problem_state, model_name="gemini-1.5-flash"
    )

    if not strategies:
        print("\n[FAILURE] Failed to generate strategic blueprint. Exiting.")
        return

    print(f"[SUCCESS] Generated {len(strategies)} strategies.")
    strategy_names = [s.get("strategy_name", "Unnamed Strategy") for s in strategies]
    for i, name in enumerate(strategy_names):
        print(f"  {i + 1}. {name}")

    print("\nGenerated strategies (JSON):")
    print(json.dumps(strategies, indent=2, ensure_ascii=False))

    # 2. Embed Strategies using Ollama
    # --------------------------------
    print("\nStep 2: Embedding generated strategies using Ollama...")
    embedded_strategies = embed_strategies(strategies)

    if not embedded_strategies or not all(
        "embedding" in s and s["embedding"] for s in embedded_strategies
    ):
        print("\n[FAILURE] Failed to embed strategies using Ollama. Exiting.")
        return

    print("[SUCCESS] Strategies embedded successfully.")

    # 3. Calculate Similarity Matrix
    # ------------------------------
    print("\nStep 3: Calculating cosine similarity matrix...")
    similarity_matrix = calculate_similarity_matrix(embedded_strategies)

    if similarity_matrix.size == 0:
        print("\n[FAILURE] Failed to calculate similarity matrix.")
        return

    print("[SUCCESS] Similarity matrix calculated.")

    # 4. Display Results
    # ------------------
    print("\n--- Final Results ---")
    print("Strategy Names:")
    for i, name in enumerate(strategy_names):
        print(f"  {i}: {name}")

    print("\nCosine Similarity Matrix:")
    np.set_printoptions(precision=4, suppress=True)
    print(similarity_matrix)

    print("\n--- Test Script Finished ---")


if __name__ == "__main__":
    main()
