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
