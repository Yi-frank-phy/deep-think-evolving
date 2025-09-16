import json
import os
from typing import Any

import numpy as np

from src.context_manager import (
    append_step,
    create_context,
    generate_summary,
    record_reflection,
)
from src.strategy_architect import generate_strategic_blueprint
from src.embedding_client import embed_strategies
from src.diversity_calculator import calculate_similarity_matrix


def main() -> None:
    """Run the end-to-end test pipeline for strategy generation and analysis."""
    print("--- Running Full Pipeline Test Script (Gemini + Ollama) ---")

    # Ensure the Gemini API key is available before attempting generation.
    if not os.environ.get("GEMINI_API_KEY"):
        print("\n[ERROR] GEMINI_API_KEY environment variable is not set.")
        print("This script requires a Google Gemini API key for the generation step.")
        print("\nPlease set the environment variable before running:")
        print("  export GEMINI_API_KEY='your_google_api_key_here'")
        print("\nScript finished without execution.")
        return

    # 1. Generate Strategic Blueprints
    # ---------------------------------
    problem_state = (
        "我们正在开发一个大型语言模型驱动的自主研究代理。"
        "当前进展：代理可以分解问题、执行网络搜索并阅读文档。"
        "遇到的困境：当面对需要综合来自多个来源的矛盾信息才能得出结论的复杂问题时，"
        "代理的性能会急剧下降。它经常会陷入其中一个信源的观点，或者无法形成一个连贯的最终答案。"
    )
    print(f"\nProblem State:\n{problem_state}")
    print("\nStep 1: Generating strategic blueprint (using Gemini)...")

    # Per the model usage policy for testing, use the 'lite' version.
    # Note: Using gemini-1.5-flash as a stand-in for the hypothetical gemini-2.5-flash-lite
    strategies = generate_strategic_blueprint(
        problem_state, model_name="gemini-1.5-flash"
    )

    if not strategies:
        print("\n[FAILURE] Failed to generate strategic blueprint. Exiting.")
        return

    print(f"[SUCCESS] Generated {len(strategies)} strategies.")
    strategy_names = [s.get("strategy_name", "Unnamed Strategy") for s in strategies]
    for i, name in enumerate(strategy_names):
        print(f"  {i + 1}. {name}")

    print("\nGenerated strategies (JSON):")
    print(json.dumps(strategies, indent=2, ensure_ascii=False))

    print("\nStep 1b: Initialising per-strategy reasoning contexts...")
    thread_registry: list[dict] = []
    for idx, strategy in enumerate(strategies, start=1):
        thread_id = f"strategy-{idx:02d}"
        context_path = create_context(thread_id)
        append_step(
            thread_id,
            {
                "event": "strategy_initialised",
                "strategy_name": strategy.get("strategy_name"),
                "rationale": strategy.get("rationale"),
                "initial_assumption": strategy.get("initial_assumption"),
            },
        )
        thread_registry.append(
            {
                "thread_id": thread_id,
                "context_path": str(context_path),
                "strategy": strategy,
            }
        )
        print(f"  → Context ready for {thread_id} at {context_path}")

    # 2. Embed Strategies using Ollama
    # --------------------------------
    print("\nStep 2: Embedding generated strategies using Ollama...")
    embedded_strategies = embed_strategies(strategies)

    if not embedded_strategies or not all(
        "embedding" in s and s["embedding"] for s in embedded_strategies
    ):
        print("\n[FAILURE] Failed to embed strategies using Ollama. Exiting.")
        return

    print("[SUCCESS] Strategies embedded successfully.")

    for idx, strategy in enumerate(embedded_strategies, start=1):
        thread_id = thread_registry[idx - 1]["thread_id"]
        embedding = strategy.get("embedding") or []
        append_step(
            thread_id,
            {
                "event": "embedding_generated",
                "embedding_dimensions": len(embedding),
                "embedding_preview": embedding[:8],
            },
        )

    # 3. Calculate Similarity Matrix
    # ------------------------------
    print("\nStep 3: Calculating cosine similarity matrix...")
    similarity_matrix = calculate_similarity_matrix(embedded_strategies)

    if similarity_matrix.size == 0:
        print("\n[FAILURE] Failed to calculate similarity matrix.")
        return

    print("[SUCCESS] Similarity matrix calculated.")

    # 4. Display Results
    # ------------------
    print("\n--- Final Results ---")
    print("Strategy Names:")
    for i, name in enumerate(strategy_names):
        print(f"  {i}: {name}")

    print("\nCosine Similarity Matrix:")
    np.set_printoptions(precision=4, suppress=True)
    print(similarity_matrix)

    if similarity_matrix.size:
        for idx, registry_entry in enumerate(thread_registry):
            append_step(
                registry_entry["thread_id"],
                {
                    "event": "similarity_scores",
                    "scores": similarity_matrix[idx].tolist(),
                },
            )

    print("\nStep 4: Generating SoC summaries for downstream agents...")
    for registry_entry in thread_registry:
        summary_result = generate_summary(registry_entry["thread_id"])
        registry_entry["summary"] = summary_result
        print(
            "  → Summary updated for",
            f" {registry_entry['thread_id']} (stored at {summary_result.path})",
        )

    print("\nStep 5: Evaluating whether to persist long-term reflections...")
    reflection_candidates: dict[str, dict[str, Any]] = {}

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

    if not reflection_candidates:
        print("  → No reflection agents were triggered in this run.")
    else:
        for thread_id, payload in reflection_candidates.items():
            entry = thread_registry[payload["thread_index"]]
            outcome = payload["outcome"]
            append_step(
                thread_id,
                {
                    "event": "reflection_triggered",
                    "outcome": outcome,
                    "reasons": payload["reasons"],
                    "metadata": payload["metadata"],
                },
            )

            reflection_text = (
                f"Reflection checkpoint for {thread_id}: {outcome}. "
                f"Triggers: {'; '.join(payload['reasons'])}. "
                "Consult the working summary for detailed state before proceeding."
            )

            reflection_path = record_reflection(
                thread_id,
                reflection_text,
                outcome=outcome,
                metadata={"reasons": payload["reasons"], "events": payload["metadata"]},
            )

            print(
                "  → Long-term reflection stored for",
                f" {thread_id} at {reflection_path}",
            )

    print("\n--- Test Script Finished ---")


if __name__ == "__main__":
    main()
