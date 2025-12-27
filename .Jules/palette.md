## 2024-05-23 - Chat Log Accessibility
**Learning:** For dynamic chat interfaces, `role="log"` combined with `aria-live="polite"` and `aria-atomic="false"` is critical. Without `aria-atomic="false"`, some screen readers might re-read the entire chat history on every update, which is a severe usability issue.
**Action:** Always verify `aria-atomic="false"` when implementing live regions for append-only lists like chat logs or activity feeds.
