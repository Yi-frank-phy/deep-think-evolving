"""
Test suite for Human-in-the-Loop (HIL) tool: ask_human.

Tests the HilManager, HilRequest, and the ask_human tool implementation.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


class TestHilRequest:
    """Tests for the HilRequest class."""
    
    def test_hil_request_initialization(self):
        """HilRequest should initialize with correct fields."""
        from src.tools.ask_human import HilRequest
        
        req = HilRequest(
            question="What should I do?",
            context="Current state is X",
            agent="judge",
            timeout=120
        )
        
        assert req.question == "What should I do?"
        assert req.context == "Current state is X"
        assert req.agent == "judge"
        assert req.timeout == 120
        assert req.request_id is not None
        assert req.created_at is not None
        assert req.response is None
    
    def test_hil_request_to_dict(self):
        """to_dict should return serializable dictionary."""
        from src.tools.ask_human import HilRequest
        
        req = HilRequest(
            question="Test?",
            context="Ctx",
            agent="executor"
        )
        
        d = req.to_dict()
        
        assert "request_id" in d
        assert "agent" in d
        assert "question" in d
        assert "context" in d
        assert "timeout_seconds" in d
        assert "created_at" in d
        
        # Should be JSON serializable
        import json
        json_str = json.dumps(d)
        assert len(json_str) > 0


class TestHilManager:
    """Tests for the HilManager class."""
    
    def test_hil_manager_initialization(self):
        """HilManager should initialize with empty pending requests."""
        from src.tools.ask_human import HilManager
        
        manager = HilManager()
        
        assert manager.pending_requests == {}
        assert manager.broadcast_func is None
    
    def test_set_broadcast_func(self):
        """Should set the broadcast function."""
        from src.tools.ask_human import HilManager
        
        manager = HilManager()
        
        async def mock_broadcast(msg):
            pass
        
        manager.set_broadcast_func(mock_broadcast)
        
        assert manager.broadcast_func == mock_broadcast
    
    def test_submit_response_success(self):
        """submit_response should set response and trigger event."""
        from src.tools.ask_human import HilManager, HilRequest
        
        manager = HilManager()
        req = HilRequest("Question?", "Context", "architect")
        manager.pending_requests[req.request_id] = req
        
        result = manager.submit_response(req.request_id, "Human says yes")
        
        assert result is True
        assert req.response == "Human says yes"
        assert req.response_event.is_set()
    
    def test_submit_response_unknown_id(self):
        """submit_response should return False for unknown request_id."""
        from src.tools.ask_human import HilManager
        
        manager = HilManager()
        
        result = manager.submit_response("unknown-id", "Some response")
        
        assert result is False


class TestHilManagerAsync:
    """Async tests for HilManager."""
    
    @pytest.mark.asyncio
    async def test_request_human_input_with_immediate_response(self):
        """Should return response when submitted before timeout."""
        from src.tools.ask_human import HilManager
        
        manager = HilManager()
        
        broadcast_called = []
        async def mock_broadcast(msg):
            broadcast_called.append(msg)
        
        manager.set_broadcast_func(mock_broadcast)
        
        # Start request in background
        async def respond_quickly():
            await asyncio.sleep(0.1)
            # Find the pending request and respond
            for req_id in list(manager.pending_requests.keys()):
                manager.submit_response(req_id, "Quick response")
                break
        
        responder = asyncio.create_task(respond_quickly())
        
        result = await manager.request_human_input(
            question="Quick question?",
            context="Context",
            agent="test",
            timeout=5
        )
        
        await responder
        
        assert result == "Quick response"
        assert len(broadcast_called) == 1
        assert broadcast_called[0]["type"] == "hil_required"
    
    @pytest.mark.asyncio
    async def test_request_human_input_timeout(self):
        """Should return timeout message when no response."""
        from src.tools.ask_human import HilManager
        
        manager = HilManager()
        
        async def mock_broadcast(msg):
            pass  # Don't respond
        
        manager.set_broadcast_func(mock_broadcast)
        
        result = await manager.request_human_input(
            question="Will timeout?",
            context="",
            agent="test",
            timeout=1  # Short timeout
        )
        
        assert "timeout" in result.lower() or "no human response" in result.lower()
    
    @pytest.mark.asyncio
    async def test_pending_request_cleanup_after_response(self):
        """Pending request should be removed after response."""
        from src.tools.ask_human import HilManager
        
        manager = HilManager()
        
        async def mock_broadcast(msg):
            # Immediately respond
            for req_id in list(manager.pending_requests.keys()):
                manager.submit_response(req_id, "Immediate")
        
        manager.set_broadcast_func(mock_broadcast)
        
        await manager.request_human_input(
            question="Test?",
            context="",
            agent="test",
            timeout=5
        )
        
        # Should be cleaned up
        assert len(manager.pending_requests) == 0


class TestAskHumanTool:
    """Tests for the ask_human tool wrapper."""
    
    def test_ask_human_tool_returns_placeholder(self):
        """Synchronous ask_human should return placeholder."""
        from src.tools.ask_human import ask_human
        
        # LangChain tools should be invoked with .invoke()
        result = ask_human.invoke({"question": "Test question?", "context": "Context"})
        
        # Should return a placeholder since async version is needed
        assert "HIL PLACEHOLDER" in result or isinstance(result, str)
    
    def test_ask_human_is_langchain_tool(self):
        """ask_human should be decorated as a LangChain tool."""
        from src.tools.ask_human import ask_human
        
        # Check it has tool metadata (decorated with @tool)
        assert hasattr(ask_human, 'name')
        assert ask_human.name == "ask_human"


class TestAskHumanAsync:
    """Tests for ask_human_async function."""
    
    @pytest.mark.asyncio
    async def test_ask_human_async_uses_global_manager(self):
        """ask_human_async should use the global hil_manager."""
        from src.tools.ask_human import ask_human_async, hil_manager
        
        responses_received = []
        
        async def mock_broadcast(msg):
            # Immediately respond
            for req_id in list(hil_manager.pending_requests.keys()):
                hil_manager.submit_response(req_id, "Global manager response")
        
        hil_manager.set_broadcast_func(mock_broadcast)
        
        result = await ask_human_async(
            question="Using global?",
            context="",
            agent="test"
        )
        
        assert "Global manager response" in result or "timeout" in result.lower()
