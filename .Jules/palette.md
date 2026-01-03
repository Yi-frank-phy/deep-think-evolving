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

## 2025-06-03 - [TaskGraph Empty State]
**Learning:** Empty states in data visualization components are prime real estate for user education. Replacing a generic "Waiting..." message with a descriptive, icon-rich call-to-action significantly improves perceived polish and usability.
**Action:** Avoid generic empty states. Use the space to explain *what* will happen and *how* to trigger it, using consistent iconography to reinforce the visual language.

## 2025-06-15 - [Global Utility for Animations]
**Learning:** Local <style> blocks in components for simple animations (like spinners) pollute the component code and lead to inconsistency.
**Action:** Move standard animations to global utility classes (e.g., .animate-spin) in src/styles/main.css to ensure reuse and cleaner component code.

## 2025-06-15 - [Live Regions for Logs]
**Learning:** Fast-updating logs (like thinking processes) are invisible to screen readers unless marked as live regions.
**Action:** Add role="log" and aria-live="polite" to containers that stream text updates to ensure screen reader users can follow the process.
