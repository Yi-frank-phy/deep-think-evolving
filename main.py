import asyncio
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Use the new graph with evolution loop
from src.core.graph_builder import build_deep_think_graph
from src.logging_utils import emit_spec_event


def parse_args(argv: Optional[list[str]] = None) -> Namespace:
    parser = ArgumentParser(description="Run the Deep Think Evolving pipeline.")
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
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum evolution iterations before termination.",
    )
    # NOTE: --temperature-coupling removed. LLM temperature is always 1.0.
    # System temperature τ controls resource allocation only.
    return parser.parse_args(argv)


async def run_pipeline(args: Namespace) -> None:
    """Run the end-to-end Deep Think Evolving pipeline with evolution loop."""

    print("--- Running Deep Think Evolving Pipeline ---")

    problem_state = (
        "我们正在开发一个大型语言模型驱动的自主研究代理。"
        "当前进展：代理可以分解问题、执行网络搜索并阅读文档。"
        "遇到的困境：当面对需要综合来自多个来源的矛盾信息才能得出结论的复杂问题时，"
        "代理的性能会急剧下降。它经常会陷入其中一个信源的观点，或者无法形成一个连贯的最终答案。"
    )
    print(f"\nProblem State:\n{problem_state}")

    # Build and compile the graph with evolution loop
    app = build_deep_think_graph()

    # Initial state matching DeepThinkState
    initial_state = {
        "problem_state": problem_state,
        "strategies": [],
        "research_context": None,
        "spatial_entropy": float("inf"),  # Start high, converge low
        "effective_temperature": 1.0,
        "normalized_temperature": 0.5,
        "config": {
            "max_iterations": args.max_iterations,
            "entropy_threshold": 0.1,
            "total_child_budget": 6,
            "t_max": 2.0,
            "c_explore": 1.0,
            # NOTE: LLM temperature is always 1.0 (Logic Manifold Integrity)
        },
        "virtual_filesystem": {},
        "history": [],
        "iteration_count": 0,
    }

    print(f"\nConfig: max_iterations={args.max_iterations}")

    # Execute the graph (async for streaming support)
    try:
        final_state = await app.ainvoke(initial_state)
    except Exception as e:
        print(f"\nPipeline exited with error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Process results
    print("\n--- Pipeline Results ---")
    print(f"Iterations completed: {final_state.get('iteration_count', 0)}")
    print(f"Final entropy: {final_state.get('spatial_entropy', 0):.4f}")
    print(f"Final temperature (tau): {final_state.get('normalized_temperature', 0):.4f}")
    
    # Output final report
    final_report = final_state.get("final_report")
    if final_report:
        print("\n" + "=" * 60)
        print("📝 最终报告")
        print("=" * 60)
        print(final_report)
        print("=" * 60)

    
    strategies = final_state.get("strategies", [])
    active = [s for s in strategies if s.get("status") == "active"]
    expanded = [s for s in strategies if s.get("status") == "expanded"]
    
    print(f"Total strategies: {len(strategies)} ({len(active)} active, {len(expanded)} expanded)")
    
    # Show top strategies by score
    sorted_strategies = sorted(strategies, key=lambda x: x.get("score", 0), reverse=True)
    print("\nTop 5 Strategies:")
    for i, s in enumerate(sorted_strategies[:5]):
        print(f"  {i+1}. [{s.get('status', '?')}] {s['name']} (score: {s.get('score', 0):.3f})")

    # Process history logs
    history = final_state.get("history", [])
    
    def emit(message: str) -> None:
        print(message)

    if args.emit_spec_log:
        log_path = args.spec_log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        spec_message = f"Spec log stored at {log_path.resolve()}"
        emit_spec_event(emit, "FILE", spec_message)
        log_path.write_text("\n".join(history) + "\n", encoding="utf-8")

    print("\n--- Pipeline Finished ---")


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the Deep Think Evolving pipeline."""
    args = parse_args(argv)
    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()

