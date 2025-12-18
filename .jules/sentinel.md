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
