"""Utility to materialise Codex integration tasks as structured JSON files."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class CodexTask:
    """Represents a Codex integration task definition."""

    task_id: str
    title: str
    source_branch: str
    integration_branch: str
    owner: str
    status: str
    description: str
    steps: List[str]
    validation_commands: List[str]
    acceptance_criteria: List[str]

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["steps"] = list(self.steps)
        payload["validation_commands"] = list(self.validation_commands)
        payload["acceptance_criteria"] = list(self.acceptance_criteria)
        return payload


TASK_REGISTRY: tuple[CodexTask, ...] = (
    CodexTask(
        task_id="T-012",
        title="Integrate google grounding search branch with mainline spec",
        source_branch="codex/implement-google-grounding-search-functionality",
        integration_branch="integration/codex-google-grounding",
        owner="Codex Integration Pod",
        status="ready",
        description=(
            "Create an integration branch for the Google grounding capability, merge the latest main "
            "updates, and resolve conflicts while retaining CONTEXT_HISTORY_LIMIT and offline mode "
            "clauses before adding the new grounding requirements."
        ),
        steps=[
            "git fetch --all --prune",
            "git checkout -b integration/codex-google-grounding origin/codex/implement-google-grounding-search-functionality",
            "git merge origin/main",
            "List conflicted files with git status and git diff --name-only --diff-filter=U",
            "Resolve conflicts giving priority to CONTEXT_HISTORY_LIMIT and offline mode language from main",
            "Incorporate Google Grounding interface notes into docs/spec-kit/spec.md §3.3/§3.4",
            "Update docs/spec-kit/tasks.md to mark T-007 Done after integration",
        ],
        validation_commands=[
            "specify check",
            "pytest",
            "pytest -m smoke",
            "npm run test",
        ],
        acceptance_criteria=[
            "Conflicts are documented with root causes for each touched file",
            "Merged spec retains latest mainline constraints while adding Google grounding requirements",
            "All validation commands succeed and logs are captured for the integration record",
        ],
    ),
    CodexTask(
        task_id="T-013",
        title="Integrate logging helper and acceptance report branch",
        source_branch="codex/add-logging-helper-and-generate-acceptance-report",
        integration_branch="integration/codex-acceptance-report",
        owner="Codex Integration Pod",
        status="ready",
        description=(
            "Merge the logging helper branch with main, preserving CONTEXT_HISTORY_LIMIT and offline mode sections "
            "while extending observability and acceptance criteria in the spec."
        ),
        steps=[
            "git fetch --all --prune",
            "git checkout -b integration/codex-acceptance-report origin/codex/add-logging-helper-and-generate-acceptance-report",
            "git merge origin/main",
            "Capture conflict inventory and explain causes in the task log",
            "Keep mainline CONTEXT_HISTORY_LIMIT/offline clauses and append logging + acceptance script notes to docs/spec-kit/spec.md",
            "Extend README usage notes if new helper scripts require invocation instructions",
            "Update docs/spec-kit/tasks.md to mark T-011 Done after integration",
        ],
        validation_commands=[
            "specify check",
            "pytest",
            "pytest -m smoke",
            "npm run test",
        ],
        acceptance_criteria=[
            "Conflict resolution summary lists every file and rationale",
            "Spec and README reflect logging helper workflows without regressing mainline clauses",
            "Post-merge validation commands succeed with collected evidence",
        ],
    ),
    CodexTask(
        task_id="T-014",
        title="Batch integrate remaining codex feature branches",
        source_branch="codex/*",
        integration_branch="integration/codex-*",
        owner="Codex Integration Pod",
        status="ready",
        description=(
            "Iteratively create integration branches for every outstanding codex feature branch, merging main first, "
            "tracking conflicts, and synchronising new requirements back into the spec and tasks ledger."
        ),
        steps=[
            "git fetch --all --prune",
            "Enumerate codex/* branches with git branch -r --list 'codex/*'",
            "For each branch create integration/<branch> and merge origin/main",
            "Document conflicts and explain causes before resolution",
            "Preserve latest CONTEXT_HISTORY_LIMIT/offline clauses during every conflict fix",
            "Backport new feature requirements into docs/spec-kit/spec.md and relevant README sections",
            "Update docs/spec-kit/tasks.md entries (e.g., T-008+) to reflect completion status",
        ],
        validation_commands=[
            "specify check",
            "pytest",
            "pytest -m smoke",
            "npm run test",
        ],
        acceptance_criteria=[
            "Every codex branch produces a conflict log and integration summary",
            "Spec kit documents are synchronised with all new requirements without losing mainline terms",
            "Quality gates succeed after each integration batch",
        ],
    ),
)


def initiate_codex_tasks(base_dir: Path | None = None, *, force: bool = True) -> list[Path]:
    """Materialise all Codex tasks into JSON files and return the created paths."""

    root = base_dir or Path(__file__).resolve().parents[1]
    tasks_dir = root / "codex_tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for task in TASK_REGISTRY:
        target = tasks_dir / f"{task.task_id.lower()}.json"
        if target.exists() and not force:
            continue
        target.write_text(
            json.dumps(task.to_payload(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        created.append(target)
    return created


def _main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-force",
        action="store_true",
        help="Do not overwrite existing task files; skip ones that already exist.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    created = initiate_codex_tasks(force=not args.no_force)

    if not created:
        print("No Codex tasks were created (files already existed).")
    else:
        print("Created/updated Codex tasks:")
        for path in created:
            print(f" - {path.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(_main())
