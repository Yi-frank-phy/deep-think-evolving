# AGENTS.md

## 🧠 Single Source of Truth
- **Primary Documentation**: `DESIGN.md` (or `SPECS/*.md`) is the absolute source of truth.
- **Conflict Resolution**: If the code behaves differently than the documentation, **the code is wrong**, unless the documentation is explicitly marked as "outdated".
- **Role Definition**: You are a "Pure AI Implementation" system. Humans write docs; AI writes code. Your job is to bridge this gap strictly.

## 🛡️ Consistency & Auditing
- When running auditing tasks, do not fix the code immediately unless asked. Instead, produce a report.
- Ignore "style" issues (linting, formatting). Focus purely on **Business Logic**, **Data Structures**, and **Missing Features**.
