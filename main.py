import os
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from src.agent_graph import build_graph
from src.logging_utils import emit_spec_event


def parse_args(argv: Optional[list[str]] = None) -> Namespace:
    parser = ArgumentParser(description="Run the Deep Think acceptance pipeline.")
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
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    """Run the end-to-end test pipeline for strategy generation and analysis."""

    args = parse_args(argv)

    print("--- Running Full Pipeline (LangChain + LangGraph) ---")

    problem_state = (
        "我们正在开发一个大型语言模型驱动的自主研究代理。"
        "当前进展：代理可以分解问题、执行网络搜索并阅读文档。"
        "遇到的困境：当面对需要综合来自多个来源的矛盾信息才能得出结论的复杂问题时，"
        "代理的性能会急剧下降。它经常会陷入其中一个信源的观点，或者无法形成一个连贯的最终答案。"
    )
    print(f"\nProblem State:\n{problem_state}")

    # Build and compile the graph
    app = build_graph()

    # Initial state
    initial_state = {
        "problem_state": problem_state,
        "strategies": [],
        "embedded_strategies": [],
        "similarity_matrix": [],
        "summaries": {},
        "logs": [],
        "thread_registry": [],
    }

    # Execute the graph
    try:
        final_state = app.invoke(initial_state)
    except Exception as e:
        print(f"\nPipeline exited early with error: {e}")
        return

    # Process logs and results
    logs = final_state.get("logs", [])
    
    # Emit spec events for logs
    def emit(message: str) -> None:
        print(message)

    for log in logs:
        emit_spec_event(emit, "INFO", log)

    if args.emit_spec_log:
        log_path = args.spec_log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        spec_message = f"Spec log stored at {log_path.resolve()}"
        emit_spec_event(emit, "FILE", spec_message)
        log_path.write_text("\n".join(logs) + "\n", encoding="utf-8")

    print("\n--- Pipeline Finished ---")


if __name__ == "__main__":
    main()
