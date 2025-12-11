from __future__ import annotations

import os
from typing import Optional

import numpy as np
import requests

# ModelScope Qwen3-Embedding-8B configuration
DEFAULT_MODELSCOPE_API_ENDPOINT = "https://api-inference.modelscope.cn/v1/embeddings"
DEFAULT_MODELSCOPE_MODEL = "Qwen/Qwen3-Embedding-8B"
MODELSCOPE_API_KEY_ENV = "MODELSCOPE_API_KEY"
EMBEDDING_DIMENSION = 4096  # Qwen3-Embedding-8B max dimension

USE_MOCK_ENV_VAR = "USE_MOCK_EMBEDDING"
MOCK_DIM_ENV_VAR = "MOCK_EMBEDDING_DIM"
DEFAULT_MOCK_DIM = 4096  # Updated to match Qwen3-Embedding-8B
_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def _is_truthy(value: Optional[str]) -> bool:
    """Return True when the given environment string represents truthy."""

    return bool(value) and value.strip().lower() in _TRUTHY_VALUES


def _resolve_use_mock(explicit: Optional[bool]) -> bool:
    """Determine whether mock embeddings should be used."""

    if explicit is not None:
        return explicit
    return _is_truthy(os.environ.get(USE_MOCK_ENV_VAR))


def _mock_embedding_dimension() -> int:
    """Read the mock embedding dimensionality from the environment."""

    raw_value = os.environ.get(MOCK_DIM_ENV_VAR)
    if raw_value:
        try:
            dimension = int(raw_value)
            if dimension > 0:
                return dimension
            print(
                f"[WARNING] {MOCK_DIM_ENV_VAR} must be positive; received {raw_value!r}. "
                f"Falling back to {DEFAULT_MOCK_DIM}."
            )
        except ValueError:
            print(
                f"[WARNING] {MOCK_DIM_ENV_VAR} value {raw_value!r} is not an integer. "
                f"Falling back to {DEFAULT_MOCK_DIM}."
            )
    return DEFAULT_MOCK_DIM


def _apply_mock_embeddings(strategies: list[dict]) -> list[dict]:
    """Populate each strategy with a randomly generated embedding."""

    dimension = _mock_embedding_dimension()
    for strategy in strategies:
        strategy["embedding"] = np.random.rand(dimension).tolist()
    return strategies


def _get_modelscope_embedding(text: str, api_key: str, endpoint: str, model: str, dimensions: int = None) -> list[float]:
    """Call ModelScope embedding API (OpenAI-compatible format)."""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "input": text,
        "encoding_format": "float"  # Required by ModelScope API
    }
    
    # Some APIs support dimensions parameter, but it's optional
    if dimensions:
        payload["dimensions"] = dimensions
    
    response = requests.post(endpoint, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    
    result = response.json()
    # OpenAI-compatible format: {"data": [{"embedding": [...]}], ...}
    if "data" in result and len(result["data"]) > 0:
        return result["data"][0].get("embedding", [])
    return []


def embed_strategies(strategies: list[dict], use_mock: Optional[bool] = None) -> list[dict]:
    """Embed strategies using ModelScope Qwen3-Embedding-8B or generated mock vectors.

    Args:
        strategies: Strategy dictionaries produced by ``generate_strategic_blueprint``.
        use_mock: Optional explicit toggle for mock embeddings. When ``None``, the
            ``USE_MOCK_EMBEDDING`` environment variable is consulted.

    Returns:
        The same list of strategies enriched with an ``embedding`` key, or an empty
        list when an error occurs.
    """

    if not strategies:
        return []

    if _resolve_use_mock(use_mock):
        print("  (Using mock embedding data)...")
        return _apply_mock_embeddings(strategies)

    api_key = os.environ.get(MODELSCOPE_API_KEY_ENV)
    if not api_key:
        print(f"\n[ERROR] {MODELSCOPE_API_KEY_ENV} environment variable is not set.")
        print("Please set MODELSCOPE_API_KEY to use ModelScope Qwen3-Embedding-8B.")
        return []

    endpoint = os.environ.get("MODELSCOPE_API_ENDPOINT", DEFAULT_MODELSCOPE_API_ENDPOINT)
    model = os.environ.get("MODELSCOPE_EMBEDDING_MODEL", DEFAULT_MODELSCOPE_MODEL)

    for i, strategy in enumerate(strategies):
        document_to_embed = (
            f"Strategy: {strategy.get('strategy_name', '')}\n"
            f"Rationale: {strategy.get('rationale', '')}\n"
            f"Assumption: {strategy.get('initial_assumption', '')}"
        )

        try:
            print(
                f"  Embedding strategy {i + 1}/{len(strategies)} using ModelScope: "
                f"'{strategy.get('strategy_name', 'N/A')}'..."
            )
            
            embedding = _get_modelscope_embedding(document_to_embed, api_key, endpoint, model)
            
            if not embedding:
                print("\n[ERROR] ModelScope response is missing the 'embedding' field.")
                strategy["embedding"] = []
                continue

            strategy["embedding"] = embedding
            print(f"  ...Success ({len(embedding)} dimensions).")

        except requests.exceptions.ConnectionError as error:
            print(f"\n[ERROR] Could not connect to ModelScope server at {endpoint}.")
            print(f"Underlying error: {error}")
            return []
        except requests.exceptions.Timeout as error:
            print(f"\n[ERROR] ModelScope request timed out when embedding strategy {i + 1}: {error}")
            strategy["embedding"] = []
            continue
        except requests.exceptions.HTTPError as error:
            print(f"\n[ERROR] HTTP error during embedding: {error}")
            try:
                print(f"Response from server: {response.text}")
            except:
                pass
            strategy["embedding"] = []
            continue
        except requests.exceptions.RequestException as error:
            print(f"\n[ERROR] Unexpected network error during embedding strategy {i + 1}: {error}")
            strategy["embedding"] = []
            continue
        except Exception as error:  # pragma: no cover - defensive guard
            print(f"\n[ERROR] An unexpected error occurred during embedding strategy {i + 1}: {error}")
            strategy["embedding"] = []
            continue

    return strategies


def embed_text(document: str) -> list[float]:
    """Generate an embedding vector for an arbitrary document string."""

    if not document.strip():
        return []

    # Check for mock
    if _resolve_use_mock(None):
        dim = _mock_embedding_dimension()
        return np.random.rand(dim).tolist()

    api_key = os.environ.get(MODELSCOPE_API_KEY_ENV)
    if not api_key:
        print(f"[ERROR] {MODELSCOPE_API_KEY_ENV} not set. Cannot embed text.")
        return []

    endpoint = os.environ.get("MODELSCOPE_API_ENDPOINT", DEFAULT_MODELSCOPE_API_ENDPOINT)
    model = os.environ.get("MODELSCOPE_EMBEDDING_MODEL", DEFAULT_MODELSCOPE_MODEL)

    try:
        return _get_modelscope_embedding(document, api_key, endpoint, model)
    except Exception as error:
        print(f"[ERROR] Failed to embed text: {error}")
        return []


