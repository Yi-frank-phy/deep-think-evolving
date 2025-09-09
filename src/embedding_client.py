import os
import time
import numpy as np
import google.generativeai as genai

def embed_strategies(strategies: list[dict], use_mock: bool = False) -> list[dict]:
    """
    Embeds a list of strategies using the Gemini embedding model or a mock.

    Args:
        strategies: A list of strategy dictionaries.
        use_mock: If True, generates random vectors instead of calling the API.

    Returns:
        A list of strategies, each with a new 'embedding' key.
    """
    if not strategies:
        return []

    # --- Mocking Logic ---
    if use_mock:
        print("  (Using mock embedding data)...")
        for strategy in strategies:
            # Gemini embedding-001 has a dimension of 768.
            strategy['embedding'] = np.random.rand(768).tolist()
        return strategies

    # --- Real API Logic (with rate-limiting) ---
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set for embedding.")
        return []

    genai.configure(api_key=api_key)

    for i, strategy in enumerate(strategies):
        document_to_embed = (
            f"Strategy: {strategy['strategy_name']}\n"
            f"Rationale: {strategy['rationale']}\n"
            f"Assumption: {strategy['initial_assumption']}"
        )

        try:
            print(f"  Embedding strategy {i+1}/{len(strategies)}: '{strategy['strategy_name']}'...")

            result = genai.embed_content(
                model="models/embedding-001",
                content=document_to_embed,
                task_type="RETRIEVAL_DOCUMENT"
            )

            strategy['embedding'] = result['embedding']

            print("  ...Success. Waiting 1 second.")
            time.sleep(1)

        except Exception as e:
            print(f"\nAn error occurred during embedding strategy {i+1}: {e}")
            return []

    return strategies
