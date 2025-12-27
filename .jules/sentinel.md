## 2024-05-25 - WebSocket Connection Exhaustion
**Vulnerability:** The WebSocket endpoint was susceptible to connection exhaustion (DoS) because there was no limit on the number of concurrent connections per IP.
**Learning:** WebSocket connections are persistent and resource-intensive. Without rate limiting or concurrency limits, a single malicious actor can consume all available file descriptors or memory.
**Prevention:** Implement a `WebSocketRateLimiter` that tracks active connections per IP and rejects new ones when a threshold is reached. Also, ensure periodic cleanup of stale connection data.

## 2024-05-23 - SPA Fallback Masking API Errors
**Vulnerability:** The SPA fallback route `serve_spa` was catching all unmatched requests, including those to `/api/`, and returning `index.html` (200 OK) instead of 404.
**Learning:** SPA catch-all routes can inadvertently mask API misconfigurations or missing endpoints, making debugging harder and potentially confusing automated tools/scanners.
**Prevention:** Explicitly check for API prefixes (e.g., `api/`) in the catch-all route and return 404 immediately if matched.
