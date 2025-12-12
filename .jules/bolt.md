## 2024-02-14 - Chat List Virtualization Opportunity
**Learning:** The chat message list re-renders entirely on every keystroke and streaming chunk because `messages` state updates create new array references.
**Action:** Implemented `React.memo` on individual `MessageItem` components. This prevents re-rendering of previous messages when a new chunk arrives or when the input field is typed into. This is a crucial optimization for long-running chat sessions.
