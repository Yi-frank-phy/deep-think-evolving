from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from main import run_pipeline
from src.context_manager import SummaryResult


def test_run_pipeline_success(tmp_path):
    logs: List[str] = []

    def logger(message: str) -> None:
        logs.append(message)

    strategies = [
        {"strategy_name": "Alpha", "rationale": "r1", "initial_assumption": "a1"},
        {"strategy_name": "Beta", "rationale": "r2", "initial_assumption": "a2"},
    ]

    append_events: List[Dict[str, Any]] = []
    reflections: List[Dict[str, Any]] = []

    def validate_api_key() -> bool:
        return True

    def generate_blueprint(_: str) -> List[dict]:
        return strategies

    def create_context(thread_id: str) -> Path:
        path = tmp_path / thread_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def append_step(thread_id: str, payload: dict) -> Path:
        append_events.append({"thread_id": thread_id, "payload": payload})
        context_dir = tmp_path / thread_id
        context_dir.mkdir(parents=True, exist_ok=True)
        history = context_dir / "history.log"
        history.touch()
        return history

    def embed_strategies(items: List[dict]) -> List[dict]:
        for index, item in enumerate(items):
            if index == 0:
                item["embedding"] = [1.0, 0.0]
            else:
                item["embedding"] = [0.0, 1.0]
        return items

    def calculate_similarity_matrix(_: List[dict]) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, 1.0]])

    def generate_summary(thread_id: str) -> SummaryResult:
        path = tmp_path / thread_id / "summary.md"
        path.write_text("summary", encoding="utf-8")
        return SummaryResult(path=path, text="summary")

    def record_reflection(thread_id: str, *_args, **kwargs) -> Path:
        path = tmp_path / f"{thread_id}-reflection.json"
        path.write_text("{}", encoding="utf-8")
        reflections.append({"thread_id": thread_id, **kwargs})
        return path

    adapters = {
        "validate_api_key": validate_api_key,
        "generate_blueprint": generate_blueprint,
        "create_context": create_context,
        "append_step": append_step,
        "embed_strategies": embed_strategies,
        "calculate_similarity_matrix": calculate_similarity_matrix,
        "generate_summary": generate_summary,
        "record_reflection": record_reflection,
        "logger": logger,
    }

    result = run_pipeline("problem", adapters=adapters)

    assert result["status"] == "success"
    assert len(result["strategies"]) == 2
    assert any(event["payload"]["event"] == "similarity_scores" for event in append_events)
    assert reflections
    assert logs


def test_run_pipeline_missing_api_key():
    messages: List[str] = []

    def logger(message: str) -> None:
        messages.append(message)

    result = run_pipeline(
        "problem",
        adapters={"validate_api_key": lambda: False, "logger": logger},
    )

    assert result["status"] == "missing_api_key"
    assert any("GEMINI_API_KEY" in line for line in messages)
