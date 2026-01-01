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
