
import os
from fastapi.testclient import TestClient

# We need to set the env var BEFORE importing the server for the first time
# or reload it. Since pytest runs this, we rely on monkeypatch mostly,
# but for the "default" case, we want to ensure it works without env var.
# Ideally we import app inside the test functions or fixtures, but app is module global.

def test_cors_allowed_origin():
    """Verify that requests from allowed origins are accepted."""
    from server import app
    client = TestClient(app)

    # Assuming default localhost:5173 is allowed
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"

def test_cors_disallowed_origin():
    """Verify that requests from disallowed origins are not allowed."""
    from server import app
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://evil-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # The status code might still be 200 (OK), but the Access-Control-Allow-Origin header should be missing
    assert "access-control-allow-origin" not in response.headers

def test_cors_custom_env_var(monkeypatch):
    """Verify that ALLOWED_ORIGINS env var works."""
    # Reload server module to pick up new env var
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://trusted-site.com,https://another-trusted.com")

    import server
    import importlib
    importlib.reload(server)

    client = TestClient(server.app)

    response = client.options(
        "/health",
        headers={
            "Origin": "https://trusted-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://trusted-site.com"

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173", # Should be disallowed now
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in response.headers
