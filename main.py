import json
import os
from typing import Any, Callable, Mapping, Optional

import numpy as np

from src.context_manager import (
    SummaryResult,
    append_step,
    create_context,
    generate_summary,
    record_reflection,
)
from src.diversity_calculator import calculate_similarity_matrix
from src.embedding_client import embed_strategies
from src.strategy_architect import generate_strategic_blueprint


Logger = Callable[[str], None]


def _default_logger(message: str) -> None:
    print(message)


def _default_validate_api_key() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def _default_generate_blueprint(problem_state: str) -> list[dict[str, Any]]:
    # Per the model usage policy for testing, use the 'lite' version.
    # Note: Using gemini-1.5-flash as a stand-in for the hypothetical gemini-2.5-flash-lite
    return generate_strategic_blueprint(problem_state, model_name="gemini-1.5-flash")


DEFAULT_ADAPTERS: dict[str, Any] = {
    "validate_api_key": _default_validate_api_key,
    "generate_blueprint": _default_generate_blueprint,
    "create_context": create_context,
    "append_step": append_step,
    "embed_strategies": embed_strategies,
    "calculate_similarity_matrix": calculate_similarity_matrix,
    "generate_summary": generate_summary,
    "record_reflection": record_reflection,
    "logger": _default_logger,
}


def run_pipeline(
    problem_state: str, *, adapters: Optional[Mapping[str, Any]] = None
) -> dict[str, Any]:
    """Execute the strategy pipeline and return structured telemetry for testing."""

    config: dict[str, Any] = dict(DEFAULT_ADAPTERS)
    if adapters:
        config.update(adapters)

    logger: Logger = config.get("logger", _default_logger)
    log_messages: list[str] = []

    def emit(message: str) -> None:
        log_messages.append(message)
        logger(message)

    if not config["validate_api_key"]():
        error_message = "GEMINI_API_KEY environment variable is not set."
        emit("\n[ERROR] GEMINI_API_KEY environment variable is not set.")
        emit("This script requires a Google Gemini API key for the generation step.")
        emit("\nPlease set the environment variable before running:")
        emit("  export GEMINI_API_KEY='your_google_api_key_here'")
        emit("\nScript finished without execution.")
        return {"status": "missing_api_key", "error": error_message, "logs": log_messages}

    emit("\nStep 1: Generating strategic blueprint (using Gemini)...")
    strategies = config["generate_blueprint"](problem_state)

    if not strategies:
        emit("\n[FAILURE] Failed to generate strategic blueprint. Exiting.")
        return {
            "status": "blueprint_failed",
            "error": "Strategy generation returned no results.",
            "logs": log_messages,
        }

    strategy_names = [s.get("strategy_name", "Unnamed Strategy") for s in strategies]
    emit(f"[SUCCESS] Generated {len(strategies)} strategies.")
    for i, name in enumerate(strategy_names, start=1):
        emit(f"  {i}. {name}")

    emit("\nGenerated strategies (JSON):")
    emit(json.dumps(strategies, indent=2, ensure_ascii=False))

    emit("\nStep 1b: Initialising per-strategy reasoning contexts...")
    thread_registry: list[dict[str, Any]] = []
    create_context_fn = config["create_context"]
    append_step_fn = config["append_step"]
    for idx, strategy in enumerate(strategies, start=1):
        thread_id = f"strategy-{idx:02d}"
        context_path = create_context_fn(thread_id)
        append_step_fn(
            thread_id,
            {
                "event": "strategy_initialised",
                "strategy_name": strategy.get("strategy_name"),
                "rationale": strategy.get("rationale"),
                "initial_assumption": strategy.get("initial_assumption"),
                "milestones": strategy.get("milestones", {}),
            },
        )
        thread_registry.append(
            {
                "thread_id": thread_id,
                "context_path": context_path,
                "strategy": strategy,
            }
        )
        emit(f"  → Context ready for {thread_id} at {context_path}")

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


def main() -> None:
    """Run the end-to-end test pipeline for strategy generation and analysis."""

    print("--- Running Full Pipeline Test Script (Gemini + Ollama) ---")

    problem_state = (
        "我们正在开发一个大型语言模型驱动的自主研究代理。"
        "当前进展：代理可以分解问题、执行网络搜索并阅读文档。"
        "遇到的困境：当面对需要综合来自多个来源的矛盾信息才能得出结论的复杂问题时，"
        "代理的性能会急剧下降。它经常会陷入其中一个信源的观点，或者无法形成一个连贯的最终答案。"
    )
    print(f"\nProblem State:\n{problem_state}")

    result = run_pipeline(problem_state)
    if result.get("status") != "success":
        print(f"\nPipeline exited early: {result.get('error', 'Unknown error')}")
        return

    print("\n--- Test Script Finished ---")


if __name__ == "__main__":
    main()
