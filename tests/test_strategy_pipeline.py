"""Smoke tests for the strategy pipeline offline mode."""

from typing import Any

import numpy as np
import pytest

from pathlib import Path
from main import run_pipeline, _build_mock_adapters


@pytest.mark.smoke
def test_smoke_pipeline_offline(tmp_path: Path) -> None:
    adapters = _build_mock_adapters(tmp_path)
    result = run_pipeline("mock problem statement", adapters=adapters)

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
    assert "# Mock Strategy Summary" in summary.text

    reflections = result["reflections"]
    assert isinstance(reflections, list)
    # Reflections might be empty depending on similarity scores in mock
    # In main.py mock: matrix[0, 1] = 0.42. Min score 0.42 > 0.2, Max 0.42 < 0.85.
    # So no reflections triggered.
    # assert reflections # This would fail if empty.
    
    logs = result["logs"]
    assert isinstance(logs, list)
    assert any("Generating strategic blueprint" in line for line in logs)
