## 2024-12-23 - Input Validation on Batch Operations
**Vulnerability:** The `ForceSynthesizeRequest` endpoint accepted an unbounded list of strategy IDs, which could lead to resource exhaustion or log flooding (DoS) if a malicious actor sent a massive list.
**Learning:** Even internal-facing or "HIL" (Human-in-the-Loop) endpoints need strict input validation limits. Logging user input (like a list of IDs) without size limits is a specific risk vector.
**Prevention:** Use Pydantic's `min_length` and `max_length` validators on all list fields in API request models.
## 2024-05-22 - Path Traversal in Static File Serving
**Vulnerability:** The `serve_spa` endpoint used `DIST_DIR / full_path` without validating that the resolved path remained inside `DIST_DIR`. This allowed attackers to access arbitrary files on the system using `..` (path traversal) characters (e.g., `%2e%2e/etc/passwd`).
**Learning:** `pathlib`'s `/` operator does not automatically prevent path traversal. It just joins paths. Always use `.resolve()` and check `.relative_to(base_dir)` when serving files based on user input.
**Prevention:**
```python
file_path = (BASE_DIR / input_path).resolve()
try:
    file_path.relative_to(BASE_DIR.resolve())
except ValueError:
    raise SecurityException("Path traversal detected")
```

## 2024-05-25 - Memory Exhaustion in Rate Limiter
**Vulnerability:** The `SimpleRateLimiter` stored request timestamps in a dictionary keyed by client IP. The dictionary keys were never removed, allowing an attacker to exhaust server memory by sending requests from many unique (spoofed) IPs.
**Learning:** In-memory stateful logic must always have a bounding mechanism (cleanup/eviction) to prevent unbounded growth. Python's `defaultdict` automatically creates keys on access, which makes this pattern easy to miss.
**Prevention:** Implement periodic cleanup of stale keys and a hard limit (cap) on the number of stored clients.
```python
if len(self.request_counts) > self.max_clients:
    self.request_counts.clear() # Emergency purge
```
