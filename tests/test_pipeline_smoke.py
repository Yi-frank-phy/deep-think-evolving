"""Smoke tests for verifying the end-to-end strategy pipeline."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.strategy_architect import generate_strategic_blueprint
from src.embedding_client import embed_strategies
from src.diversity_calculator import calculate_similarity_matrix


pytestmark = pytest.mark.smoke

OLLAMA_HEALTH_URL = os.environ.get("OLLAMA_HEALTH_URL", "http://localhost:11434/api/tags")
_TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}


def _has_gemini_api_key() -> bool:
    """Return ``True`` when the Gemini API key is available."""

    return bool(os.environ.get("GEMINI_API_KEY"))


def _use_mock_embeddings() -> bool:
    """Return True when mock embeddings are enabled via environment flag."""

    return os.environ.get("USE_MOCK_EMBEDDING", "").strip().lower() in _TRUTHY_ENV_VALUES


def _is_ollama_running() -> bool:
    """Check whether the local Ollama service responds on the expected port."""

    try:
        response = requests.get(OLLAMA_HEALTH_URL, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


@pytest.fixture(scope="module")
def ensure_environment() -> None:
    """Skip the smoke suite when required services are not available."""

    if not _has_gemini_api_key():
        pytest.skip("GEMINI_API_KEY environment variable is not set.")

    if not _use_mock_embeddings() and not _is_ollama_running():
        pytest.skip(f"Ollama service is not reachable at {OLLAMA_HEALTH_URL}.")


def _assert_strategy_schema(strategies: Iterable[dict]) -> None:
    for strategy in strategies:
        assert isinstance(strategy, dict), "Each strategy must be a dictionary."
        for key in ("strategy_name", "rationale", "initial_assumption"):
            assert key in strategy, f"Missing '{key}' in strategy: {strategy}"


def _assert_embeddings(strategies: Iterable[dict]) -> None:
    for strategy in strategies:
        assert "embedding" in strategy, "Embedding missing from strategy."
        embedding = strategy["embedding"]
        assert isinstance(embedding, (list, tuple)), "Embedding must be a sequence of floats."
        assert len(embedding) > 0, "Embedding cannot be empty."


def test_pipeline_smoke(ensure_environment: None) -> None:
    """Run the strategic pipeline and validate returned data structures."""

    problem_state = "团队正在探索改进复杂研究任务的自动化能力。"

    strategies = generate_strategic_blueprint(problem_state)
    assert isinstance(strategies, list)
    assert strategies, "Strategy list should not be empty."
    _assert_strategy_schema(strategies)

    embedded_strategies = embed_strategies(strategies, use_mock=_use_mock_embeddings())
    assert isinstance(embedded_strategies, list)
    assert embedded_strategies, "Embedding step returned no strategies."
    assert len(embedded_strategies) == len(strategies)
    _assert_embeddings(embedded_strategies)

    similarity_matrix = calculate_similarity_matrix(embedded_strategies)
    assert isinstance(similarity_matrix, np.ndarray)
    expected_size = len(embedded_strategies)
    assert similarity_matrix.shape == (expected_size, expected_size)

