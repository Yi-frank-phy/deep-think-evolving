
import pytest
from fastapi.testclient import TestClient
import server

client = TestClient(server.app)

def test_api_404_not_masked_by_spa():
    """Test that non-existent API routes return 404 JSON, not 200 HTML."""
    response = client.get("/api/non_existent_endpoint")

    # Ideally this should be 404
    # But currently we suspect it is 200 OK (index.html)
    if response.status_code == 200 and "<!doctype html>" in response.text.lower():
        print("\nVULNERABILITY CONFIRMED: /api/non_existent_endpoint returned HTML instead of 404")
        assert False, "API 404 masked by SPA fallback"

    assert response.status_code == 404
