## 2024-05-25 - WebSocket Connection Exhaustion (DoS)
**Vulnerability:** The WebSocket endpoints `/ws/simulation` and `/ws/knowledge_base` had no limits on the number of concurrent connections or connection rate. An attacker could open thousands of connections, exhausting server file descriptors and memory (DoS).
**Learning:** Standard HTTP rate limiters (like `SimpleRateLimiter`) usually rely on `HTTPException`, which cannot be raised inside a WebSocket handshake or loop. WebSockets require dedicated lifecycle management (accept/close) and concurrency tracking since connections are persistent.
**Prevention:**
1.  Implement a `WebSocketRateLimiter` that tracks both *connection attempts* (rate) and *active connections* (concurrency).
2.  Use `await websocket.close(code=1008)` to reject connections instead of raising HTTP exceptions.
3.  Ensure the limiter cleans up state on `disconnect`.
4.  Avoid `defaultdict` side-effects in cleanup loops that can cause memory leaks.

## 2025-05-27 - SPA Fallback Masking API Errors
**Vulnerability:** The SPA catch-all route (`/{full_path:path}`) blindly returned `index.html` for any unmatched path, including invalid API endpoints (e.g., `/api/v2/unknown`). This caused API clients to receive a 200 OK HTML response instead of a 404 JSON error, potentially breaking client-side logic that expects JSON.
**Learning:** In full-stack applications serving an SPA from the backend, the "catch-all" handler must explicitly exclude API namespaces. FastAPI's route matching order sends everything not matched by a specific API route to the catch-all.
**Prevention:**
1.  In the SPA fallback handler, verify the path does not start with the API prefix (e.g., `api/`).
2.  Explicitly raise `HTTPException(404)` for unmatched API routes to provide correct status codes and prevent confusion.
## 2026-01-01 - Numerical Range DoS Vulnerability
**Vulnerability:** The `SimulationConfig` Pydantic model lacked numerical range validation (e.g., `ge`, `le`). Attackers could submit excessively large values (e.g., `beam_width=10000`, `max_iterations=1000000`), forcing the server to allocate massive graph structures and run infinite loops, leading to memory/CPU exhaustion (DoS).
**Learning:** Pydantic's type hints (`int`) validate *types* but not *values*. For resource-intensive parameters (iterations, budget, buffer sizes), explicit `Field(..., le=MAX)` constraints are mandatory to prevent resource exhaustion attacks.
**Prevention:** Always use `pydantic.Field` with `gt/ge` and `lt/le` constraints for any numerical input that affects loop counters, memory allocation, or complexity.
## 2026-01-05 - Rate Limiter Global Reset Vulnerability
**Vulnerability:** The `SimpleRateLimiter` and `WebSocketRateLimiter` implemented a "Safety Valve" that cleared *all* client history (`self.request_counts.clear()`) when the client limit was reached. An attacker could exploit this by flooding the server with requests from spoofed IPs to hit the limit, triggering a global reset that wiped the rate limit history for *all* users (including the attacker), effectively bypassing the rate limit.
**Learning:** Security controls that "fail open" or reset completely under stress are valid attack targets. A "safety valve" for memory protection must degrade gracefully (e.g., pruning old entries) rather than failing into an insecure state (resetting checks).
**Prevention:**
1.  Implement LRU (Least Recently Used) or similar pruning strategies to remove *only* a subset of entries when capacity is reached.
2.  Never use `.clear()` on security-critical state tables unless the service is restarting.
3.  Add tests specifically for "overflow" conditions to ensure the security control maintains integrity under load.
