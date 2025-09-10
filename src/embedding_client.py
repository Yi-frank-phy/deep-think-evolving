import os
import json
import requests
import numpy as np

OLLAMA_API_ENDPOINT = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL = "dengcao/Qwen3-Embedding-8B:Q4_K_M"

def embed_strategies(strategies: list[dict]) -> list[dict]:
    """
    Embeds a list of strategies using a local Ollama embedding model.

    This function takes a list of strategy dictionaries, prepares the text content
    from each, and calls the local Ollama API to get their vector embeddings.

    Args:
        strategies: A list of strategy dictionaries. Each dict is expected to
                    have 'strategy_name', 'rationale', and 'initial_assumption'.

    Returns:
        A list of the same strategy dictionaries, with a new 'embedding' key
        added to each, containing the embedding vector. Returns an empty list
        if an error occurs.
    """
    if not strategies:
        return []

    headers = {'Content-Type': 'application/json'}

    for i, strategy in enumerate(strategies):
        # Prepare the document for a single strategy
        document_to_embed = (
            f"Strategy: {strategy.get('strategy_name', '')}\n"
            f"Rationale: {strategy.get('rationale', '')}\n"
            f"Assumption: {strategy.get('initial_assumption', '')}"
        )

        payload = {
            "model": EMBEDDING_MODEL,
            "prompt": document_to_embed
        }

        try:
            print(f"  Embedding strategy {i+1}/{len(strategies)} using Ollama: '{strategy.get('strategy_name', 'N/A')}'...")

            # Make the POST request to the local Ollama server
            response = requests.post(OLLAMA_API_ENDPOINT, headers=headers, data=json.dumps(payload))
            response.raise_for_status()

            response_json = response.json()
            strategy['embedding'] = response_json.get('embedding')

            print("  ...Success.")

        except requests.exceptions.ConnectionError as e:
            print(f"\n[ERROR] Could not connect to Ollama server at {OLLAMA_API_ENDPOINT}.")
            print("Please ensure the Ollama service is running and the model has been pulled.")
            print(f"  (e.g., 'ollama pull {EMBEDDING_MODEL}')")
            print(f"Underlying error: {e}")
            return []
        except requests.exceptions.HTTPError as e:
            print(f"\n[ERROR] HTTP Error during embedding: {e}")
            print(f"Response from server: {response.text}")
            if "model not found" in response.text:
                print(f"Model '{EMBEDDING_MODEL}' not found. Please ensure the model is available via 'ollama list'.")
            return []
        except Exception as e:
            print(f"\nAn unexpected error occurred during embedding strategy {i+1}: {e}")
            return []

    return strategies
