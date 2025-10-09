"""Smoke tests for the strategy pipeline offline mode."""

from typing import Any

import numpy as np
import pytest

from main import run_pipeline


@pytest.mark.smoke
def test_smoke_pipeline_offline() -> None:
    result = run_pipeline("mock problem statement", use_mock=True)

    assert result["status"] == "success"
    strategies = result["strategies"]
    assert isinstance(strategies, list) and strategies
    assert all("strategy_name" in item for item in strategies)

    similarity_matrix = result["similarity_matrix"]
    assert isinstance(similarity_matrix, np.ndarray)
    assert similarity_matrix.shape == (
        len(strategies),
        len(strategies),
    )

    summaries: dict[str, Any] = result["summaries"]
    assert summaries
    summary = next(iter(summaries.values()))
    assert summary.text.startswith("Mock summary")

    reflections = result["reflections"]
    assert isinstance(reflections, list) and reflections
    first_reflection = reflections[0]
    assert "thread_id" in first_reflection
    assert "path" in first_reflection
    assert "outcome" in first_reflection

    logs = result["logs"]
    assert isinstance(logs, list)
    assert any("Generating strategic blueprint" in line for line in logs)
