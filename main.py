import json
import os
from argparse import ArgumentParser, Namespace
from pathlib import Path
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
from src.logging_utils import emit_spec_event


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

    def spec_emit(tag: str, message: str) -> None:
        emit_spec_event(emit, tag, message)

    if not config["validate_api_key"]():
        error_message = "GEMINI_API_KEY environment variable is not set."
        spec_emit("ERR", "GEMINI_API_KEY environment variable is not set.")
        spec_emit(
            "GUIDE",
            "This script requires a Google Gemini API key for the generation step.",
        )
        spec_emit(
            "GUIDE",
            "Please set the environment variable before running: \n  export GEMINI_API_KEY='your_google_api_key_here'",
        )
        spec_emit("ERR", "Script finished without execution.")
        return {"status": "missing_api_key", "error": error_message, "logs": log_messages}

    spec_emit("STEP", "Step 1: Generating strategic blueprint (using Gemini)...")
    strategies = config["generate_blueprint"](problem_state)

    if not strategies:
        spec_emit("ERR", "Failed to generate strategic blueprint. Exiting.")
        return {
            "status": "blueprint_failed",
            "error": "Strategy generation returned no results.",
            "logs": log_messages,
        }

    strategy_names = [s.get("strategy_name", "Unnamed Strategy") for s in strategies]
    spec_emit("OK", f"Generated {len(strategies)} strategies.")
    spec_emit("DATA", "Generated strategies (JSON):")
    spec_emit("DATA", json.dumps(strategies, indent=2, ensure_ascii=False))

    spec_emit("STEP", "Step 1b: Initialising per-strategy reasoning contexts...")
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
        spec_emit(
            "CTX",
            (
                f"Context ready for {thread_id} at {context_path} "
                f"(milestones logged: {len(milestones)})"
            ),
        )

    for i, name in enumerate(strategy_names, start=1):
        spec_emit("DATA", f"Strategy {i}: {name}")

    spec_emit("STEP", "Step 2: Embedding generated strategies using Ollama...")
    embedded_strategies = config["embed_strategies"](strategies)

    if not embedded_strategies or not all(
        "embedding" in s and s["embedding"] for s in embedded_strategies
    ):
        spec_emit("ERR", "Failed to embed strategies using Ollama. Exiting.")
        return {
            "status": "embedding_failed",
            "error": "Embedding stage returned empty results.",
            "thread_registry": thread_registry,
            "logs": log_messages,
        }

    spec_emit("OK", "Strategies embedded successfully.")

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

    spec_emit("STEP", "Step 3: Calculating cosine similarity matrix...")
    similarity_matrix = config["calculate_similarity_matrix"](embedded_strategies)

    if not isinstance(similarity_matrix, np.ndarray) or similarity_matrix.size == 0:
        spec_emit("ERR", "Failed to calculate similarity matrix.")
        return {
            "status": "similarity_failed",
            "error": "Similarity calculation produced no data.",
            "thread_registry": thread_registry,
            "embedded_strategies": embedded_strategies,
            "logs": log_messages,
        }

    spec_emit("OK", "Similarity matrix calculated.")

    spec_emit("SUMMARY", "--- Final Results ---")
    spec_emit("SUMMARY", "Strategy Names:")
    for i, name in enumerate(strategy_names):
        spec_emit("DATA", f"{i}: {name}")

    spec_emit("SUMMARY", "Cosine Similarity Matrix:")
    matrix_str = np.array2string(similarity_matrix, precision=4, suppress_small=True)
    spec_emit("DATA", matrix_str)

    for idx, registry_entry in enumerate(thread_registry):
        append_step_fn(
            registry_entry["thread_id"],
            {
                "event": "similarity_scores",
                "scores": similarity_matrix[idx].tolist(),
            },
        )

    spec_emit("STEP", "Step 4: Generating SoC summaries for downstream agents...")
    summary_results: dict[str, SummaryResult] = {}
    generate_summary_fn = config["generate_summary"]
    for registry_entry in thread_registry:
        summary_result = generate_summary_fn(registry_entry["thread_id"])
        registry_entry["summary"] = summary_result
        summary_results[registry_entry["thread_id"]] = summary_result
        spec_emit(
            "FILE",
            (
                f"Summary updated for {registry_entry['thread_id']} "
                f"(stored at {summary_result.path})"
            ),
        )

    spec_emit("STEP", "Step 5: Evaluating whether to persist long-term reflections...")
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
        spec_emit("INFO", "No reflection agents were triggered in this run.")
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

            spec_emit(
                "FILE",
                f"Long-term reflection stored for {thread_id} at {reflection_path}",
            )

            reflections.append(
                {
                    "thread_id": thread_id,
                    "path": reflection_path,
                    "outcome": payload["outcome"],
                    "reasons": list(payload["reasons"]),
                }
            )

    spec_emit("OK", "Pipeline execution completed.")

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


def _build_mock_adapters(base_dir: Path) -> Mapping[str, Any]:
    base_dir.mkdir(parents=True, exist_ok=True)

    def validate_api_key() -> bool:
        return True

    def generate_blueprint(_: str) -> list[dict[str, Any]]:
        return [
            {
                "strategy_name": "Divergent Research Threads",
                "rationale": "Establish parallel investigations for contested facts.",
                "initial_assumption": "Multiple viewpoints must be reconciled via evidence weighting.",
                "milestones": [
                    "Collect primary sources",
                    "Score credibility",
                    "Synthesize consensus",
                ],
            },
            {
                "strategy_name": "Moderated Debate Loop",
                "rationale": "Use an arbiter to merge findings from each expert persona.",
                "initial_assumption": "A structured dialogue will surface contradictions early.",
                "milestones": [
                    "Draft debate agenda",
                    "Run synthesis round",
                ],
            },
        ]

    def create_context(thread_id: str) -> Path:
        path = base_dir / thread_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def append_step(thread_id: str, payload: dict[str, Any]) -> Path:
        context_dir = base_dir / thread_id
        context_dir.mkdir(parents=True, exist_ok=True)
        history = context_dir / "history.log"
        with history.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return history

    def embed_strategies(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        size = max(len(items), 1)
        for index, item in enumerate(items):
            embedding = [0.0] * size
            embedding[index % size] = 1.0
            item["embedding"] = embedding
        return items

    def calculate_similarity_matrix(items: list[dict[str, Any]]) -> np.ndarray:
        size = len(items)
        if size == 0:
            return np.array([])
        matrix = np.eye(size)
        if size >= 2:
            matrix[0, 1] = matrix[1, 0] = 0.42
        return matrix

    def generate_summary(thread_id: str) -> SummaryResult:
        summary_path = base_dir / thread_id / "summary.md"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_text = (
            "# Mock Strategy Summary\n\n"
            "This is a deterministic summary generated for acceptance testing."
        )
        summary_path.write_text(summary_text, encoding="utf-8")
        return SummaryResult(path=summary_path, text=summary_text)

    def record_reflection(thread_id: str, text: str, **kwargs: Any) -> Path:
        reflection_path = base_dir / f"{thread_id}-reflection.json"
        reflection_payload = {"thread_id": thread_id, "text": text, **kwargs}
        reflection_path.write_text(
            json.dumps(reflection_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return reflection_path

    return {
        "validate_api_key": validate_api_key,
        "generate_blueprint": generate_blueprint,
        "create_context": create_context,
        "append_step": append_step,
        "embed_strategies": embed_strategies,
        "calculate_similarity_matrix": calculate_similarity_matrix,
        "generate_summary": generate_summary,
        "record_reflection": record_reflection,
    }


def parse_args(argv: Optional[list[str]] = None) -> Namespace:
    parser = ArgumentParser(description="Run the Deep Think acceptance pipeline.")
    parser.add_argument(
        "--use-mock",
        action="store_true",
        help="Use deterministic mock adapters instead of external services.",
    )
    parser.add_argument(
        "--emit-spec-log",
        action="store_true",
        help="Persist spec-formatted logs to --spec-log-path after execution.",
    )
    parser.add_argument(
        "--spec-log-path",
        type=Path,
        default=Path("artifacts/spec_pipeline.log"),
        help="Path where spec logs should be written when --emit-spec-log is set.",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts/mock_run"),
        help="Directory used to store mock artifacts when --use-mock is enabled.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    """Run the end-to-end test pipeline for strategy generation and analysis."""

    args = parse_args(argv)

    print("--- Running Full Pipeline Test Script (Gemini + Ollama) ---")

    problem_state = (
        "我们正在开发一个大型语言模型驱动的自主研究代理。"
        "当前进展：代理可以分解问题、执行网络搜索并阅读文档。"
        "遇到的困境：当面对需要综合来自多个来源的矛盾信息才能得出结论的复杂问题时，"
        "代理的性能会急剧下降。它经常会陷入其中一个信源的观点，或者无法形成一个连贯的最终答案。"
    )
    print(f"\nProblem State:\n{problem_state}")

    adapters: Optional[Mapping[str, Any]] = None
    if args.use_mock:
        adapters = _build_mock_adapters(args.artifacts_dir)

    result = run_pipeline(problem_state, adapters=adapters)
    if args.emit_spec_log and result.get("logs"):
        log_path = args.spec_log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        spec_message = f"Spec log stored at {log_path.resolve()}"
        emit_spec_event(result["logs"].append, "FILE", spec_message)
        emit_spec_event(_default_logger, "FILE", spec_message)
        log_path.write_text("\n".join(result["logs"]) + "\n", encoding="utf-8")

    if result.get("status") != "success":
        print(f"\nPipeline exited early: {result.get('error', 'Unknown error')}")
        return


    print("\n--- Test Script Finished ---")


if __name__ == "__main__":
    main()
