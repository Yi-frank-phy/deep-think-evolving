## 2024-04-18 - [Chat Input Accessibility & Polish]
**Learning:** Replaced emoji-based buttons with `lucide-react` icons and added ARIA labels. Inline SVG icons provide better scaling and visual consistency than emojis.
**Action:** Use `lucide-react` for all future icon needs and ensure every icon-only button has an `aria-label`. Visually hidden labels for inputs are essential for screen readers when design omits visible labels.

## 2024-05-24 - [Micro-interactions & Clipboard Feedback]
**Learning:** Users lack immediate confirmation when performing actions like copying text. Adding a state-driven icon swap (Copy -> Check) provides clear, satisfying feedback.
**Action:** For all future "copy" or "save" actions, implement a 2-second visual confirmation state.
