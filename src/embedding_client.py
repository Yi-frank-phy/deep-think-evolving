import os
import google.generativeai as genai

def embed_strategies(strategies: list[dict]) -> list[dict]:
    """
    Embeds a list of strategies using the Gemini embedding model.

    This function takes a list of strategy dictionaries, prepares the text content
    from each, and calls the Gemini API to get their vector embeddings.

    Args:
        strategies: A list of strategy dictionaries. Each dict is expected to
                    have 'strategy_name', 'rationale', and 'initial_assumption'.

    Returns:
        A list of the same strategy dictionaries, with a new 'embedding' key
        added to each, containing the embedding vector. Returns an empty list
        if an error occurs or no strategies are provided.
    """
    if not strategies:
        return []

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set for embedding.")
        return []

    genai.configure(api_key=api_key)

    # Prepare the documents for embedding by concatenating the relevant fields.
    # This creates a single text block for each strategy to capture its full meaning.
    documents_to_embed = [
        f"Strategy: {s['strategy_name']}\nRationale: {s['rationale']}\nAssumption: {s['initial_assumption']}"
        for s in strategies
    ]

    try:
        # Use the confirmed embedding model name.
        # The embed_content function can handle a list of documents in a single call.
        result = genai.embed_content(
            model="models/embedding-001",
            content=documents_to_embed,
            task_type="RETRIEVAL_DOCUMENT" # or "SEMANTIC_SIMILARITY"
        )

        # Add the embedding vector back to each original strategy dictionary.
        for i, strategy in enumerate(strategies):
            strategy['embedding'] = result['embedding'][i]

        return strategies

    except Exception as e:
        print(f"An error occurred during embedding: {e}")
        return []
