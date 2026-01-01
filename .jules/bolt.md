## 2024-02-14 - Chat List Virtualization Opportunity
**Learning:** The chat message list re-renders entirely on every keystroke and streaming chunk because `messages` state updates create new array references.
**Action:** Implemented `React.memo` on individual `MessageItem` components. This prevents re-rendering of previous messages when a new chunk arrives or when the input field is typed into. This is a crucial optimization for long-running chat sessions.

## 2024-05-23 - Parallel Strategy Propagation
**Learning:** Sequential LLM calls in the `propagation` agent created a linear bottleneck during strategy expansion. Expanding 5 strategies took ~5x the latency of a single call.
**Action:** Implemented `ThreadPoolExecutor` in `propagation_node` to parallelize `generate_children_for_strategy` calls. This reduces the total expansion time to approximately `max(latency)` instead of `sum(latency)`, significantly speeding up the evolution phase when multiple strategies are active.

## 2025-05-27 - Graph Layout Memoization
**Learning:** In `TaskGraph`, the expensive BFS layout calculation was running on every state update (e.g., score changes) because it depended on the `strategies` array reference, even when the graph topology (IDs/parents) remained constant.
**Action:** Split the memoization into two steps: 1) A `topologyHash` string and `nodePositions` map that only update when the structure changes, and 2) A final node/edge generation that updates with scores/status. This eliminates redundant BFS calculations during frequent simulation updates.
