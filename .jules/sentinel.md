# Sentinel Journal

## 2024-05-22 - Overly Permissive CORS
**Vulnerability:** The FastAPI server was configured with `allow_origins=["*"]` and `allow_credentials=True`.
**Learning:** This configuration allows any website to make requests to the backend with credentials (cookies, auth headers), potentially leading to CSRF or data exfiltration.
**Prevention:** Restrict `allow_origins` to known trusted domains (e.g., localhost during dev, specific domains in prod) via environment variables.
