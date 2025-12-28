## 2024-05-25 - WebSocket Connection Exhaustion (DoS)
**Vulnerability:** The WebSocket endpoints `/ws/simulation` and `/ws/knowledge_base` had no limits on the number of concurrent connections or connection rate. An attacker could open thousands of connections, exhausting server file descriptors and memory (DoS).
**Learning:** Standard HTTP rate limiters (like `SimpleRateLimiter`) usually rely on `HTTPException`, which cannot be raised inside a WebSocket handshake or loop. WebSockets require dedicated lifecycle management (accept/close) and concurrency tracking since connections are persistent.
**Prevention:**
1.  Implement a `WebSocketRateLimiter` that tracks both *connection attempts* (rate) and *active connections* (concurrency).
2.  Use `await websocket.close(code=1008)` to reject connections instead of raising HTTP exceptions.
3.  Ensure the limiter cleans up state on `disconnect`.
4.  Avoid `defaultdict` side-effects in cleanup loops that can cause memory leaks.

## 2024-05-25 - Simulation Configuration DoS
**Vulnerability:** The `SimulationConfig` Pydantic model lacked range validation for integer fields like `max_iterations`, `total_child_budget`, and `beam_width`. An attacker could submit extremely large values (e.g., 1,000,000), causing the server to spawn excessive threads or loops, leading to resource exhaustion (DoS).
**Learning:** Pydantic models used in API requests MUST have strict `ge` (greater than or equal) and `le` (less than or equal) constraints on all numerical fields that influence loop counts, memory allocation, or thread creation. Type hints alone (`int`) are insufficient for security.
**Prevention:**
1. Always use `Field(..., ge=X, le=Y)` for numerical inputs.
2. Review all loop conditions and resource allocations to ensure they are bounded by validated config values.
