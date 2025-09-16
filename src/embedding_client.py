import json
from typing import Optional

import requests

OLLAMA_API_ENDPOINT = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL = "dengcao/Qwen3-Embedding-8B:Q4_K_M"


def _request_embedding(payload: dict) -> Optional[list[float]]:
    """Perform the HTTP request to Ollama and return the embedding vector."""

    try:
        response = requests.post(
            OLLAMA_API_ENDPOINT, headers={"Content-Type": "application/json"}, data=json.dumps(payload)
        )
        response.raise_for_status()
        response_json = response.json()
        embedding = response_json.get("embedding")
        if not isinstance(embedding, list):
            return []
        return embedding
    except requests.exceptions.ConnectionError as exc:
        print(
            f"\n[ERROR] Could not connect to Ollama server at {OLLAMA_API_ENDPOINT}.\n"
            "Ensure the Ollama service is running and the embedding model is pulled."
        )
        print(f"Underlying error: {exc}")
        return []
    except requests.exceptions.HTTPError as exc:
        print(f"\n[ERROR] HTTP Error during embedding: {exc}")
        print(f"Response from server: {getattr(exc.response, 'text', '')}")
        return []
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"\n[ERROR] Unexpected error while requesting embedding: {exc}")
        return []


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

    for i, strategy in enumerate(strategies):
        # Prepare the document for a single strategy
        document_to_embed = (
            f"Strategy: {strategy.get('strategy_name', '')}\n"
            f"Rationale: {strategy.get('rationale', '')}\n"
            f"Assumption: {strategy.get('initial_assumption', '')}"
        )

        try:
            print(f"  Embedding strategy {i+1}/{len(strategies)} using Ollama: '{strategy.get('strategy_name', 'N/A')}'...")
            payload = {"model": EMBEDDING_MODEL, "prompt": document_to_embed}
            strategy['embedding'] = _request_embedding(payload)
            print("  ...Success.")
        except Exception as e:
            print(f"\nAn unexpected error occurred during embedding strategy {i+1}: {e}")
            return []

    return strategies


def embed_text(document: str) -> list[float]:
    """Generate an embedding vector for an arbitrary document string."""

    if not document.strip():
        return []

    payload = {"model": EMBEDDING_MODEL, "prompt": document}
    embedding = _request_embedding(payload)
    return embedding or []
