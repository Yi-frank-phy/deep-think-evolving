import json
import pytest
from fastapi.testclient import TestClient
import server
from unittest.mock import MagicMock

client = TestClient(server.app)

class TestServerSecurity:

    def test_chat_stream_invalid_model_name(self):
        """Test that invalid model names are rejected with 422."""
        payload = {
            "message": "Hello",
            "model_name": "malicious-model-name"
        }

        # Using post since it's a streaming endpoint, but invalid input should fail immediately
        # The endpoint returns a StreamingResponse, but with valid Pydantic model it should raise RequestValidationError before that
        response = client.post("/api/chat/stream", json=payload)

        assert response.status_code == 422
        errors = response.json().get("detail", [])
        assert any("model_name" in e["loc"] for e in errors)
        assert any("Invalid model name" in e["msg"] for e in errors)

    def test_chat_stream_message_too_long(self):
        """Test that messages exceeding the max length are rejected."""
        large_message = "A" * 50001
        payload = {
            "message": large_message,
            "model_name": "gemini-2.5-flash"
        }

        response = client.post("/api/chat/stream", json=payload)

        assert response.status_code == 422
        errors = response.json().get("detail", [])
        assert any("message" in e["loc"] for e in errors)
        assert any("String should have at most" in e["msg"] for e in errors)

    def test_chat_stream_instruction_too_long(self):
        """Test that instructions exceeding the max length are rejected."""
        large_instruction = "A" * 10001
        payload = {
            "message": "Hello",
            "instruction": large_instruction,
            "model_name": "gemini-2.5-flash"
        }

        response = client.post("/api/chat/stream", json=payload)

        assert response.status_code == 422
        errors = response.json().get("detail", [])
        assert any("instruction" in e["loc"] for e in errors)

    def test_chat_stream_audio_too_large(self):
        """Test that audio exceeding the max length is rejected."""
        # Just testing string length of base64 field
        large_audio = "A" * 15_000_001
        payload = {
            "message": "Hello",
            "audio_base64": large_audio,
            "model_name": "gemini-2.5-flash"
        }

        response = client.post("/api/chat/stream", json=payload)

        assert response.status_code == 422
        errors = response.json().get("detail", [])
        assert any("audio_base64" in e["loc"] for e in errors)

    def test_expand_node_too_long(self):
        """Test that expand_node requests with overly long rationale are rejected."""
        large_rationale = "A" * 50001
        payload = {
            "rationale": large_rationale,
            "model_name": "gemini-2.5-flash"
        }

        response = client.post("/api/expand_node", json=payload)

        assert response.status_code == 422
        errors = response.json().get("detail", [])
        assert any("rationale" in e["loc"] for e in errors)

    def test_simulation_request_too_long(self):
        """Test that simulation requests with overly long problem description are rejected."""
        large_problem = "A" * 50001
        payload = {
            "problem": large_problem,
            "config": {}
        }

        response = client.post("/api/simulation/start", json=payload)

        assert response.status_code == 422
        errors = response.json().get("detail", [])
        assert any("problem" in e["loc"] for e in errors)

    def test_hil_response_too_long(self):
        """Test that HIL responses with overly long response text are rejected."""
        large_response = "A" * 50001
        payload = {
            "request_id": "req-123",
            "response": large_response
        }

        response = client.post("/api/hil/response", json=payload)

        assert response.status_code == 422
        errors = response.json().get("detail", [])
        assert any("response" in e["loc"] for e in errors)

    def test_force_synthesize_too_many_strategies(self):
        """Test that force_synthesize requests with too many strategy IDs are rejected."""
        # 101 strategy IDs should be too many (assuming we set limit to 100)
        strategy_ids = [f"strat-{i}" for i in range(101)]
        payload = {
            "strategy_ids": strategy_ids
        }

        # This should fail after we implement the fix
        response = client.post("/api/hil/force_synthesize", json=payload)

        # Currently it might return 200 (if sim running) or 400 (if not running)
        # We want it to be 422 (Unprocessable Entity) due to validation
        if response.status_code != 422:
             pytest.fail(f"Should have failed validation with 422, got {response.status_code}")

    def test_simulation_config_validation(self):
        """Test that invalid simulation config values are rejected."""
        # Case 1: max_iterations too high
        payload = {
            "problem": "Test problem",
            "config": {
                "max_iterations": 1000
            }
        }
        response = client.post("/api/simulation/start", json=payload)
        assert response.status_code == 422
        assert "max_iterations" in response.text

        # Case 2: beam_width too high
        payload["config"] = {"beam_width": 100}
        response = client.post("/api/simulation/start", json=payload)
        assert response.status_code == 422
        assert "beam_width" in response.text

        # Case 3: total_child_budget too high
        payload["config"] = {"total_child_budget": 100}
        response = client.post("/api/simulation/start", json=payload)
        assert response.status_code == 422
        assert "total_child_budget" in response.text
