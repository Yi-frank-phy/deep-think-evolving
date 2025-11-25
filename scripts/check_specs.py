import re
import sys
from pathlib import Path

def check_tasks_md(tasks_path: Path) -> bool:
    print(f"Checking {tasks_path}...")
    if not tasks_path.exists():
        print(f"[ERROR] {tasks_path} not found.")
        return False

    content = tasks_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # Regex to match task rows: | T-XXX | Description | Owner | Status | Docs |
    task_pattern = re.compile(r"^\|\s*(T-\d+)\s*\|.*\|\s*([^|]+)\s*\|$")
    
    has_error = False
    for i, line in enumerate(lines, 1):
        match = task_pattern.match(line)
        if match:
            task_id = match.group(1)
            docs_col = match.group(2).strip()
            
            if not docs_col or docs_col.lower() == "todo":
                print(f"[WARNING] Task {task_id} on line {i} is missing documentation link (found '{docs_col}').")
                # Not a hard error, but a warning
            
    print("Tasks check completed.")
    return not has_error

def main():
    base_dir = Path(__file__).resolve().parent.parent
    docs_dir = base_dir / "docs" / "spec-kit"
    tasks_md = docs_dir / "tasks.md"
    
    success = check_tasks_md(tasks_md)
    
    if success:
        print("\n[Spec-OK] All spec checks passed.")
        sys.exit(0)
    else:
        print("\n[Spec-FAIL] Spec checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
