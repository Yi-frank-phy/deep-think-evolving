## 2024-05-25 - WebSocket Connection Exhaustion (DoS)
**Vulnerability:** The WebSocket endpoints `/ws/simulation` and `/ws/knowledge_base` had no limits on the number of concurrent connections or connection rate. An attacker could open thousands of connections, exhausting server file descriptors and memory (DoS).
**Learning:** Standard HTTP rate limiters (like `SimpleRateLimiter`) usually rely on `HTTPException`, which cannot be raised inside a WebSocket handshake or loop. WebSockets require dedicated lifecycle management (accept/close) and concurrency tracking since connections are persistent.
**Prevention:**
1.  Implement a `WebSocketRateLimiter` that tracks both *connection attempts* (rate) and *active connections* (concurrency).
2.  Use `await websocket.close(code=1008)` to reject connections instead of raising HTTP exceptions.
3.  Ensure the limiter cleans up state on `disconnect`.
4.  Avoid `defaultdict` side-effects in cleanup loops that can cause memory leaks.

## 2024-05-25 - SPA Fallback Masking API Errors
**Vulnerability:** The Single Page Application (SPA) catch-all route `/{full_path:path}` returned `index.html` (200 OK) for *all* unmatched paths, including non-existent API endpoints (e.g., `/api/v1/secret`).
**Learning:** Automated security scanners and API clients rely on 404 status codes to map the application surface. Returning 200 OK (HTML) for API calls confuses tools and masks genuine configuration errors. It can also lead to confusing frontend errors (e.g., "Unexpected token < in JSON") when the UI tries to parse HTML as JSON.
**Prevention:**
1.  Explicitly exclude API paths (e.g., `api/`) from the SPA catch-all route.
2.  Return 404 for any path starting with `api/` that matches the catch-all.
3.  Always test negative cases (non-existent endpoints) to verify they fail correctly.
