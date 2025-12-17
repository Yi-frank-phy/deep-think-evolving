## 2025-05-23 - Dynamic Values in Labels
**Learning:** Including dynamic values directly in `<label>` text (e.g., "Max Iterations: 10") creates excessive noise for screen reader users, as the entire label is re-announced on every value change.
**Action:** Separate the static label text from the dynamic value display. Use `aria-valuetext` on the input for accessibility and a separate visual element (like a `<span>`) for sighted users.
