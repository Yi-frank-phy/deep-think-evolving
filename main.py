import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

import numpy as np

from logging_helper import SpecLogger, ensure_spec_logger
from src.context_manager import (
    SummaryResult,
    append_step,
    create_context,
    generate_summary,
    record_reflection,
)
from src.diversity_calculator import calculate_similarity_matrix
from src.embedding_client import embed_strategies
from src.google_grounding import (
    default_google_grounding_client_factory,
    search_google_grounding,
)
from src.strategy_architect import generate_strategic_blueprint


DEFAULT_SPEC_LOGGER = SpecLogger()


def _default_validate_api_key() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def _default_generate_blueprint(problem_state: str) -> list[dict[str, Any]]:
    # Per the model usage policy for testing, use the 'lite' version.
    # Note: Using gemini-1.5-flash as a stand-in for the hypothetical gemini-2.5-flash-lite
    return generate_strategic_blueprint(problem_state, model_name="gemini-1.5-flash")


DEFAULT_ADAPTERS: dict[str, Any] = {
    "validate_api_key": _default_validate_api_key,
    "generate_blueprint": _default_generate_blueprint,
    "google_grounding_client_factory": default_google_grounding_client_factory,
    "search_google_grounding": search_google_grounding,
    "create_context": create_context,
    "append_step": append_step,
    "embed_strategies": embed_strategies,
    "calculate_similarity_matrix": calculate_similarity_matrix,
    "generate_summary": generate_summary,
    "record_reflection": record_reflection,
    "logger": DEFAULT_SPEC_LOGGER,
}


def _mock_generate_blueprint(problem_state: str) -> list[dict[str, Any]]:
    del problem_state  # Problem state is unused for deterministic mock data.
    return [
        {
            "strategy_name": "Mock Strategy Alpha",
            "rationale": "Offline smoke test placeholder.",
            "initial_assumption": "Sufficient for pipeline verification.",
            "milestones": [
                "Capture requirements",
                "Demonstrate mock data flow",
            ],
        },
        {
            "strategy_name": "Mock Strategy Beta",
            "rationale": "Ensures similarity matrix shape > 1.",
            "initial_assumption": "Mocks avoid external dependencies.",
            "milestones": [
                "Embed fake vectors",
                "Return deterministic reflections",
            ],
        },
    ]


def _mock_embed_strategies(strategies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    embedded: list[dict[str, Any]] = []
    for index, strategy in enumerate(strategies, start=1):
        strategy_copy = dict(strategy)
        strategy_copy.setdefault("milestones", [])
        strategy_copy["embedding"] = [float(index), float(index % 2)]
        embedded.append(strategy_copy)
    return embedded


def _mock_calculate_similarity_matrix(strategies: list[dict[str, Any]]) -> np.ndarray:
    size = len(strategies)
    if size == 0:
        return np.array([])
    return np.eye(size, dtype=float)


def _mock_generate_summary(thread_id: str) -> SummaryResult:
    path = Path(f"mock_summary_{thread_id}.md")
    text = f"Mock summary for {thread_id}."
    return SummaryResult(path=path, text=text)


def _mock_record_reflection(
    thread_id: str,
    reflection_text: str,
    *,
    outcome: str,
    metadata: Optional[Mapping[str, Any]] = None,
) -> Path:
    del reflection_text, outcome, metadata
    return Path(f"mock_reflection_{thread_id}.json")


def _mock_create_context(thread_id: str) -> Path:
    return Path(f"mock_context/{thread_id}")


def _mock_append_step(thread_id: str, payload: Any) -> Path:
    del thread_id, payload
    return Path("mock_context/history.log")


MOCK_ADAPTERS: dict[str, Any] = {
    "validate_api_key": lambda: True,
    "generate_blueprint": _mock_generate_blueprint,
    "google_grounding_client_factory": lambda: None,
    "search_google_grounding": lambda *_, **__: [],
    "create_context": _mock_create_context,
    "append_step": _mock_append_step,
    "embed_strategies": _mock_embed_strategies,
    "calculate_similarity_matrix": _mock_calculate_similarity_matrix,
    "generate_summary": _mock_generate_summary,
    "record_reflection": _mock_record_reflection,
}


def run_pipeline(
    problem_state: str,
    *,
    adapters: Optional[Mapping[str, Any]] = None,
    use_mock: bool = False,
    test_mode: bool = False,
) -> dict[str, Any]:
    """Execute the strategy pipeline and return structured telemetry for testing."""

    adapters = dict(adapters or {})
    mock_from_adapters = bool(adapters.pop("use_mock", False))

    mock_enabled = use_mock or test_mode or mock_from_adapters

    config: dict[str, Any] = dict(DEFAULT_ADAPTERS)
    if mock_enabled:
        config.update(MOCK_ADAPTERS)
    if adapters:
        config.update(adapters)

    spec_logger = ensure_spec_logger(config.get("logger"))
    log_messages: list[str] = []

    def emit(message: str) -> None:
        formatted = spec_logger.emit(message)
        log_messages.append(formatted)

    if not mock_enabled and not config["validate_api_key"]():
        error_message = "GEMINI_API_KEY environment variable is not set."
        emit("\n[ERROR] GEMINI_API_KEY environment variable is not set.")
        emit("This script requires a Google Gemini API key for the generation step.")
        emit("\nPlease set the environment variable before running:")
        emit("  export GEMINI_API_KEY='your_google_api_key_here'")
        emit("\nScript finished without execution.")
        return {"status": "missing_api_key", "error": error_message, "logs": log_messages}

    emit("\nStep 1: Generating strategic blueprint (using Gemini)...")
    strategies = config["generate_blueprint"](problem_state)

    grounding_fn = config.get("search_google_grounding")
    grounding_factory = config.get("google_grounding_client_factory")

    if grounding_fn and grounding_factory:
        for strategy in strategies:
            try:
                references = grounding_fn(
                    strategy,
                    grounding_factory,
                    logger=emit,
                    use_mock=mock_enabled,
                    test_mode=test_mode,
                )
            except Exception as exc:  # pragma: no cover - defensive guard
                emit(f"[Grounding] Unexpected error while fetching references: {exc}")
                references = []

            strategy["references"] = references

    if not strategies:
        emit("\n[FAILURE] Failed to generate strategic blueprint. Exiting.")
        return {
            "status": "blueprint_failed",
            "error": "Strategy generation returned no results.",
            "logs": log_messages,
        }

    strategy_names = [s.get("strategy_name", "Unnamed Strategy") for s in strategies]
    emit(f"[SUCCESS] Generated {len(strategies)} strategies.")
    emit("\nGenerated strategies (JSON):")
    emit(json.dumps(strategies, indent=2, ensure_ascii=False))

    emit("\nStep 1b: Initialising per-strategy reasoning contexts...")
    thread_registry: list[dict[str, Any]] = []
    create_context_fn = config["create_context"]
    append_step_fn = config["append_step"]
    for idx, strategy in enumerate(strategies, start=1):
        thread_id = f"strategy-{idx:02d}"
        context_path = create_context_fn(thread_id)
        milestones = strategy.get("milestones") or []
        if not isinstance(milestones, list):
            milestones = [milestones]
        append_step_fn(
            thread_id,
            {
                "event": "strategy_initialised",
                "strategy_name": strategy.get("strategy_name"),
                "rationale": strategy.get("rationale"),
                "initial_assumption": strategy.get("initial_assumption"),
                "milestones": milestones,
            },
        )
        thread_registry.append(
            {
                "thread_id": thread_id,
                "context_path": context_path,
                "strategy": strategy,
            }
        )
        emit(
            "  → Context ready for "
            f"{thread_id} at {context_path}"
            f" (milestones logged: {len(milestones)})"
        )

    for i, name in enumerate(strategy_names, start=1):
        emit(f"  Strategy {i}: {name}")

    emit("\nStep 2: Embedding generated strategies using Ollama...")
    embedded_strategies = config["embed_strategies"](strategies)

    if not embedded_strategies or not all(
        "embedding" in s and s["embedding"] for s in embedded_strategies
    ):
        emit("\n[FAILURE] Failed to embed strategies using Ollama. Exiting.")
        return {
            "status": "embedding_failed",
            "error": "Embedding stage returned empty results.",
            "thread_registry": thread_registry,
            "logs": log_messages,
        }

    emit("[SUCCESS] Strategies embedded successfully.")

    for idx, strategy in enumerate(embedded_strategies, start=1):
        thread_id = thread_registry[idx - 1]["thread_id"]
        embedding = strategy.get("embedding") or []
        append_step_fn(
            thread_id,
            {
                "event": "embedding_generated",
                "embedding_dimensions": len(embedding),
                "embedding_preview": embedding[:8],
            },
        )

    emit("\nStep 3: Calculating cosine similarity matrix...")
    similarity_matrix = config["calculate_similarity_matrix"](embedded_strategies)

    if not isinstance(similarity_matrix, np.ndarray) or similarity_matrix.size == 0:
        emit("\n[FAILURE] Failed to calculate similarity matrix.")
        return {
            "status": "similarity_failed",
            "error": "Similarity calculation produced no data.",
            "thread_registry": thread_registry,
            "embedded_strategies": embedded_strategies,
            "logs": log_messages,
        }

    emit("[SUCCESS] Similarity matrix calculated.")

    emit("\n--- Final Results ---")
    emit("Strategy Names:")
    for i, name in enumerate(strategy_names):
        emit(f"  {i}: {name}")

    emit("\nCosine Similarity Matrix:")
    matrix_str = np.array2string(similarity_matrix, precision=4, suppress_small=True)
    emit(matrix_str)

    for idx, registry_entry in enumerate(thread_registry):
        append_step_fn(
            registry_entry["thread_id"],
            {
                "event": "similarity_scores",
                "scores": similarity_matrix[idx].tolist(),
            },
        )

    emit("\nStep 4: Generating SoC summaries for downstream agents...")
    summary_results: dict[str, SummaryResult] = {}
    generate_summary_fn = config["generate_summary"]
    for registry_entry in thread_registry:
        summary_result = generate_summary_fn(registry_entry["thread_id"])
        registry_entry["summary"] = summary_result
        summary_results[registry_entry["thread_id"]] = summary_result
        emit(
            "  → Summary updated for "
            f"{registry_entry['thread_id']} (stored at {summary_result.path})"
        )

    emit("\nStep 5: Evaluating whether to persist long-term reflections...")
    reflection_candidates: dict[str, dict[str, Any]] = {}
    record_reflection_fn = config["record_reflection"]

    def _register_reflection(
        thread_index: int, outcome: str, reason: str, metadata: dict[str, Any]
    ) -> None:
        entry = thread_registry[thread_index]
        thread_id = entry["thread_id"]
        record = reflection_candidates.setdefault(
            thread_id,
            {
                "outcome": outcome,
                "reasons": [],
                "metadata": [],
                "thread_index": thread_index,
            },
        )
        record["reasons"].append(reason)
        record["metadata"].append(metadata)
        if record["outcome"] == "success" and outcome == "failure":
            record["outcome"] = outcome

    if similarity_matrix.size:
        pair_scores: list[tuple[float, int, int]] = []
        num_threads = len(thread_registry)
        for i in range(num_threads):
            for j in range(i + 1, num_threads):
                pair_scores.append((float(similarity_matrix[i][j]), i, j))

        if pair_scores:
            min_score, min_i, min_j = min(pair_scores, key=lambda item: item[0])
            max_score, max_i, max_j = max(pair_scores, key=lambda item: item[0])

            if min_score < 0.2:
                reason = (
                    f"Divergent exploration detected (cosine {min_score:.3f}) "
                    f"between {strategy_names[min_i]} and {strategy_names[min_j]}"
                )
                _register_reflection(
                    min_i,
                    "failure",
                    reason,
                    {
                        "trigger": "low_similarity",
                        "score": float(min_score),
                        "peer_thread": thread_registry[min_j]["thread_id"],
                    },
                )

            if max_score > 0.85:
                reason = (
                    f"High-confidence alignment achieved (cosine {max_score:.3f}) "
                    f"between {strategy_names[max_i]} and {strategy_names[max_j]}"
                )
                _register_reflection(
                    max_i,
                    "success",
                    reason,
                    {
                        "trigger": "high_similarity",
                        "score": float(max_score),
                        "peer_thread": thread_registry[max_j]["thread_id"],
                    },
                )

    reflections: list[dict[str, Any]] = []
    if not reflection_candidates:
        emit("  → No reflection agents were triggered in this run.")
    else:
        for thread_id, payload in reflection_candidates.items():
            append_step_fn(
                thread_id,
                {
                    "event": "reflection_triggered",
                    "outcome": payload["outcome"],
                    "reasons": payload["reasons"],
                    "metadata": payload["metadata"],
                },
            )

            reflection_text = (
                f"Reflection checkpoint for {thread_id}: {payload['outcome']}. "
                f"Triggers: {'; '.join(payload['reasons'])}. "
                "Consult the working summary for detailed state before proceeding."
            )

            reflection_path = record_reflection_fn(
                thread_id,
                reflection_text,
                outcome=payload["outcome"],
                metadata={"reasons": payload["reasons"], "events": payload["metadata"]},
            )

            emit(
                "  → Long-term reflection stored for "
                f"{thread_id} at {reflection_path}"
            )

            reflections.append(
                {
                    "thread_id": thread_id,
                    "path": reflection_path,
                    "outcome": payload["outcome"],
                    "reasons": list(payload["reasons"]),
                }
            )

    emit("\n--- Pipeline Execution Completed ---")

    return {
        "status": "success",
        "strategies": strategies,
        "thread_registry": thread_registry,
        "embedded_strategies": embedded_strategies,
        "similarity_matrix": similarity_matrix,
        "summaries": summary_results,
        "reflections": reflections,
        "logs": log_messages,
    }


def _is_truthy(value: Optional[str]) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def main(*, use_mock: bool = False, test_mode: bool = False) -> None:
    """Run the end-to-end test pipeline for strategy generation and analysis."""

    cli_args = set(sys.argv[1:])
    cli_use_mock = "--use-mock" in cli_args
    cli_test_mode = "--test-mode" in cli_args

    env_use_mock = _is_truthy(os.getenv("USE_MOCK_PIPELINE"))
    env_test_mode = _is_truthy(os.getenv("TEST_MODE"))

    resolved_use_mock = use_mock or cli_use_mock or env_use_mock
    resolved_test_mode = test_mode or cli_test_mode or env_test_mode
    mock_enabled = resolved_use_mock or resolved_test_mode

    cli_logger = ensure_spec_logger()
    cli_logger("--- Running Full Pipeline Test Script (Gemini + Ollama) ---")

    problem_state = (
        "我们正在开发一个大型语言模型驱动的自主研究代理。"
        "当前进展：代理可以分解问题、执行网络搜索并阅读文档。"
        "遇到的困境：当面对需要综合来自多个来源的矛盾信息才能得出结论的复杂问题时，"
        "代理的性能会急剧下降。它经常会陷入其中一个信源的观点，或者无法形成一个连贯的最终答案。"
    )
    cli_logger(f"\nProblem State:\n{problem_state}")

    result = run_pipeline(
        problem_state,
        use_mock=mock_enabled,
        test_mode=resolved_test_mode,
        adapters={"logger": cli_logger},
    )
    if result.get("status") != "success":
        cli_logger(f"\nPipeline exited early: {result.get('error', 'Unknown error')}")
        return

    cli_logger("\n--- Test Script Finished ---")


if __name__ == "__main__":
    main()
