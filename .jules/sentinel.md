## 2024-05-25 - WebSocket Connection Exhaustion (DoS)
**Vulnerability:** The WebSocket endpoints `/ws/simulation` and `/ws/knowledge_base` had no limits on the number of concurrent connections or connection rate. An attacker could open thousands of connections, exhausting server file descriptors and memory (DoS).
**Learning:** Standard HTTP rate limiters (like `SimpleRateLimiter`) usually rely on `HTTPException`, which cannot be raised inside a WebSocket handshake or loop. WebSockets require dedicated lifecycle management (accept/close) and concurrency tracking since connections are persistent.
**Prevention:**
1.  Implement a `WebSocketRateLimiter` that tracks both *connection attempts* (rate) and *active connections* (concurrency).
2.  Use `await websocket.close(code=1008)` to reject connections instead of raising HTTP exceptions.
3.  Ensure the limiter cleans up state on `disconnect`.
4.  Avoid `defaultdict` side-effects in cleanup loops that can cause memory leaks.

## 2026-01-01 - Numerical Range DoS Vulnerability
**Vulnerability:** The `SimulationConfig` Pydantic model lacked numerical range validation (e.g., `ge`, `le`). Attackers could submit excessively large values (e.g., `beam_width=10000`, `max_iterations=1000000`), forcing the server to allocate massive graph structures and run infinite loops, leading to memory/CPU exhaustion (DoS).
**Learning:** Pydantic's type hints (`int`) validate *types* but not *values*. For resource-intensive parameters (iterations, budget, buffer sizes), explicit `Field(..., le=MAX)` constraints are mandatory to prevent resource exhaustion attacks.
**Prevention:** Always use `pydantic.Field` with `gt/ge` and `lt/le` constraints for any numerical input that affects loop counters, memory allocation, or complexity.
