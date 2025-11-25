<<<<<<< HEAD
import json
from typing import Optional

=======
from __future__ import annotations

import os
from typing import Optional

import numpy as np
>>>>>>> origin/ndl0ps-codex/add-smoke-tests-for-strategic-blueprint
import requests

DEFAULT_OLLAMA_API_ENDPOINT = "http://localhost:11434/api/embeddings"
DEFAULT_OLLAMA_MODEL = "dengcao/Qwen3-Embedding-8B:Q4_K_M"
USE_MOCK_ENV_VAR = "USE_MOCK_EMBEDDING"
MOCK_DIM_ENV_VAR = "MOCK_EMBEDDING_DIM"
DEFAULT_MOCK_DIM = 768
_TRUTHY_VALUES = {"1", "true", "yes", "on"}

<<<<<<< HEAD

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
=======
>>>>>>> origin/ndl0ps-codex/add-smoke-tests-for-strategic-blueprint

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


def embed_strategies(strategies: list[dict], use_mock: Optional[bool] = None) -> list[dict]:
    """Embed strategies using Ollama or generated mock vectors.

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

<<<<<<< HEAD
=======
    if _resolve_use_mock(use_mock):
        print("  (Using mock embedding data)...")
        return _apply_mock_embeddings(strategies)

    endpoint = os.environ.get("OLLAMA_API_ENDPOINT", DEFAULT_OLLAMA_API_ENDPOINT)
    model = os.environ.get("OLLAMA_EMBEDDING_MODEL", DEFAULT_OLLAMA_MODEL)

>>>>>>> origin/ndl0ps-codex/add-smoke-tests-for-strategic-blueprint
    for i, strategy in enumerate(strategies):
        document_to_embed = (
            f"Strategy: {strategy.get('strategy_name', '')}\n"
            f"Rationale: {strategy.get('rationale', '')}\n"
            f"Assumption: {strategy.get('initial_assumption', '')}"
        )

<<<<<<< HEAD
        try:
            print(f"  Embedding strategy {i+1}/{len(strategies)} using Ollama: '{strategy.get('strategy_name', 'N/A')}'...")
            payload = {"model": EMBEDDING_MODEL, "prompt": document_to_embed}
            strategy['embedding'] = _request_embedding(payload)
            print("  ...Success.")
        except Exception as e:
            print(f"\nAn unexpected error occurred during embedding strategy {i+1}: {e}")
=======
        payload = {
            "model": model,
            "prompt": document_to_embed,
        }

        try:
            print(
                "  Embedding strategy "
                f"{i + 1}/{len(strategies)} using Ollama: "
                f"'{strategy.get('strategy_name', 'N/A')}'..."
            )
            response = requests.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()

            try:
                response_json = response.json()
            except ValueError as error:
                print(
                    "\n[ERROR] Ollama response did not contain valid JSON: "
                    f"{error}"
                )
                return []

            embedding = response_json.get("embedding")
            if not embedding:
                print(
                    "\n[ERROR] Ollama response is missing the 'embedding' field."
                )
                return []

            strategy["embedding"] = embedding
            print("  ...Success.")

        except requests.exceptions.ConnectionError as error:
            print(
                f"\n[ERROR] Could not connect to Ollama server at {endpoint}."
            )
            print("Please ensure the Ollama service is running and the model has been pulled.")
            print(f"  (e.g., 'ollama pull {model}')")
            print(f"Underlying error: {error}")
            return []
        except requests.exceptions.Timeout as error:
            print(
                f"\n[ERROR] Ollama request timed out when embedding strategy {i + 1}: {error}"
            )
            return []
        except requests.exceptions.HTTPError as error:
            print(f"\n[ERROR] HTTP error during embedding: {error}")
            print(f"Response from server: {response.text}")
            if "model not found" in response.text.lower():
                print(
                    f"Model '{model}' not found. Please ensure the model is available via 'ollama list'."
                )
            return []
        except requests.exceptions.RequestException as error:
            print(
                f"\n[ERROR] Unexpected network error during embedding strategy {i + 1}: {error}"
            )
            return []
        except Exception as error:  # pragma: no cover - defensive guard
            print(
                f"\n[ERROR] An unexpected error occurred during embedding strategy {i + 1}: {error}"
            )
>>>>>>> origin/ndl0ps-codex/add-smoke-tests-for-strategic-blueprint
            return []

    return strategies


def embed_text(document: str) -> list[float]:
    """Generate an embedding vector for an arbitrary document string."""

    if not document.strip():
        return []

    payload = {"model": EMBEDDING_MODEL, "prompt": document}
    embedding = _request_embedding(payload)
    return embedding or []
