import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from server import app, ws_limiter
import websockets

# We use TestClient for some things, but for WebSocket concurrency limits
# we need real async connections or careful mocking.
# Since TestClient is synchronous/threaded, testing async concurrency is tricky.
# We will use the `repro_websocket_dos.py` logic but wrapped in a proper test structure.

@pytest.mark.asyncio
async def test_websocket_concurrency_limit():
    # We need to run the app in a way that allows multiple connections.
    # TestClient supports websockets but runs in-process.
    # Let's try to simulate connections by directly calling the limiter.

    # Reset limiter for test
    ws_limiter.active_connections.clear()
    ws_limiter.connection_attempts.clear()

    class MockWebSocket:
        def __init__(self, ip):
            self.client = type('obj', (object,), {'host': ip})

        async def close(self, code, reason=None):
            pass

    # Simulate 20 connections from same IP
    ip = "127.0.0.1"
    sockets = []

    # Fill up to the limit (20)
    for i in range(20):
        ws = MockWebSocket(ip)
        accepted = await ws_limiter.accept(ws)
        assert accepted is True, f"Connection {i+1} should be accepted"
        sockets.append(ws)

    # Try 21st connection
    ws_fail = MockWebSocket(ip)
    accepted = await ws_limiter.accept(ws_fail)
    assert accepted is False, "Connection 21 should be rejected"

    # Disconnect one
    ws_limiter.disconnect(sockets.pop())

    # Try again
    accepted = await ws_limiter.accept(ws_fail)
    assert accepted is True, "Connection should be accepted after freeing slot"

@pytest.mark.asyncio
async def test_websocket_rate_limit():
    # Reset limiter
    ws_limiter.active_connections.clear()
    ws_limiter.connection_attempts.clear()

    class MockWebSocket:
        def __init__(self, ip):
            self.client = type('obj', (object,), {'host': ip})
        async def close(self, code, reason=None):
            pass

    ip = "192.168.1.1"

    # Config is 30 per minute.
    # We simulate 30 attempts
    for i in range(30):
        ws = MockWebSocket(ip)
        # We assume we don't hit concurrency limit for this test (mock different objects? or just don't add to active?)
        # Wait, accept() adds to active. So we must use different IPs or disconnect immediately?
        # If we use same IP, concurrency limit (20) will trigger first.
        # So we need to increase concurrency limit or test rate limit with disconnects.

        # We'll simulate connect -> disconnect cycle
        accepted = await ws_limiter.accept(ws)
        assert accepted is True
        ws_limiter.disconnect(ws)

    # Now we have 30 attempts in history.
    # 31st attempt should fail due to rate limit
    ws = MockWebSocket(ip)
    accepted = await ws_limiter.accept(ws)
    assert accepted is False, "Should be rate limited"
