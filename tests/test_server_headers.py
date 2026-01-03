import pytest
from fastapi.testclient import TestClient
import server

client = TestClient(server.app)

class TestServerHeaders:
    def test_security_headers_present(self):
        """Test that new security headers are present in responses."""
        response = client.get("/health")
        assert response.status_code == 200

        # Check existing headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

        # Check for NEW headers (these will fail until implemented)
        # 1. Referrer-Policy
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

        # 2. Permissions-Policy
        assert "Permissions-Policy" in response.headers
        # We expect microphone to be allowed for self (since app uses voice input)
        # But for now just checking existence and basic structure
        assert "microphone" in response.headers["Permissions-Policy"]
