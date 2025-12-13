## 2024-04-18 - [Chat Input Accessibility & Polish]
**Learning:** Replaced emoji-based buttons with `lucide-react` icons and added ARIA labels. Inline SVG icons provide better scaling and visual consistency than emojis.
**Action:** Use `lucide-react` for all future icon needs and ensure every icon-only button has an `aria-label`. Visually hidden labels for inputs are essential for screen readers when design omits visible labels.
