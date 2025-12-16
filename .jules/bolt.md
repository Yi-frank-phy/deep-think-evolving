## 2024-02-14 - Chat List Virtualization Opportunity
**Learning:** The chat message list re-renders entirely on every keystroke and streaming chunk because `messages` state updates create new array references.
**Action:** Implemented `React.memo` on individual `MessageItem` components. This prevents re-rendering of previous messages when a new chunk arrives or when the input field is typed into. This is a crucial optimization for long-running chat sessions.

## 2024-05-23 - Parallel Strategy Propagation
**Learning:** Sequential LLM calls in the `propagation` agent created a linear bottleneck during strategy expansion. Expanding 5 strategies took ~5x the latency of a single call.
**Action:** Implemented `ThreadPoolExecutor` in `propagation_node` to parallelize `generate_children_for_strategy` calls. This reduces the total expansion time to approximately `max(latency)` instead of `sum(latency)`, significantly speeding up the evolution phase when multiple strategies are active.
