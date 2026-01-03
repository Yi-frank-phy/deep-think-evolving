## 2025-06-03 - [Chat Accessibility]
**Learning:** Chat interfaces often lack automatic announcements for incoming messages. Adding `role="log"` with `aria-live="polite"` to the message container ensures screen reader users are notified of new content without losing focus.
**Action:** Always apply `role="log"` and `aria-live` to dynamic chat or log containers.
