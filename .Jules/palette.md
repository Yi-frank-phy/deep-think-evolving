## 2025-05-23 - Dynamic Values in Labels

**Learning:** Including dynamic values directly in `<label>` text (e.g., "Max Iterations: 10") creates excessive noise for screen reader users, as the entire label is re-announced on every value change.
**Action:** Separate the static label text from the dynamic value display. Use `aria-valuetext` on the input for accessibility and a separate visual element (like a `<span>`) for sighted users.

## 2024-04-18 - [Chat Input Accessibility & Polish]

**Learning:** Replaced emoji-based buttons with `lucide-react` icons and added ARIA labels. Inline SVG icons provide better scaling and visual consistency than emojis.
**Action:** Use `lucide-react` for all future icon needs and ensure every icon-only button has an `aria-label`. Visually hidden labels for inputs are essential for screen readers when design omits visible labels.

## 2024-05-24 - [Micro-interactions & Clipboard Feedback]

**Learning:** Users lack immediate confirmation when performing actions like copying text. Adding a state-driven icon swap (Copy -> Check) provides clear, satisfying feedback.
**Action:** For all future "copy" or "save" actions, implement a 2-second visual confirmation state.

## 2025-05-27 - [Modal Accessibility]

**Learning:** Modals require explicit accessibility attributes and keyboard handling. Users expect the Escape key to close modals, and screen readers need `role="dialog"` and `aria-modal="true"` to understand the context.
**Action:** Always implement `useEffect` for Escape key handling and add ARIA attributes to modal overlays and content.
