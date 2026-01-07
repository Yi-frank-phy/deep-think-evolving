import pytest
import asyncio
import time
from fastapi import Request
from server import SimpleRateLimiter, WebSocketRateLimiter

# Mock objects
class MockClient:
    def __init__(self, host):
        self.host = host

class MockRequest:
    def __init__(self, ip):
        self.client = MockClient(ip)

@pytest.mark.asyncio
async def test_rate_limiter_reset_vulnerability():
    """
    Test that filling the rate limiter client table does NOT reset the history for everyone.
    The vulnerability was that 'clear()' was called, removing all rate limit history.
    """
    # Setup limiter with small limit for testing
    # Max 10 clients.
    limiter = SimpleRateLimiter(requests_per_minute=10, max_clients=10)

    # 1. Fill the limiter with 10 clients
    for i in range(10):
        await limiter(MockRequest(f"192.168.1.{i}"))

    assert len(limiter.request_counts) == 10

    # 2. Make one client (Client 0) hit the rate limit cap (almost)
    # We already added 1 request above. Add 9 more.
    target_ip = "192.168.1.0"
    for _ in range(9):
        await limiter(MockRequest(target_ip))

    # Verify Client 0 has 10 requests (at the limit)
    assert len(limiter.request_counts[target_ip]) == 10

    # 3. Add one more NEW client.
    # Current state: 10 clients. 10 > 10 is False.
    # So this one is added. Count becomes 11.
    await limiter(MockRequest("192.168.1.100"))
    assert len(limiter.request_counts) == 11

    # 4. Add another NEW client to trigger the safety valve
    # Current state: 11 clients. 11 > 10 is True.
    # This should trigger the cleanup logic.
    await limiter(MockRequest("192.168.1.101"))

    # 5. Verification
    # Vulnerable behavior: clear() called -> count becomes 0 -> then add new one -> count 1.
    # Secure behavior: prune called -> count becomes ~8 -> then add new one -> count 9.

    remaining_clients = len(limiter.request_counts)
    print(f"Remaining clients: {remaining_clients}")

    # If remaining_clients is 1, it means everyone else was wiped.
    if remaining_clients <= 1:
        pytest.fail("Rate limiter cleared all clients! Vulnerability exists.")

    assert remaining_clients > 1, "Rate limiter should not clear all clients on overflow"

@pytest.mark.asyncio
async def test_websocket_rate_limiter_max_clients():
    """
    Test that WebSocketRateLimiter also enforces a max_clients limit
    to prevent memory exhaustion.
    """
    ws_limiter = WebSocketRateLimiter(requests_per_minute=10, max_concurrent_per_ip=5)

    # Inject max_clients manually if not present (to test logic we are about to add)
    ws_limiter.max_clients = 10

    # Mock WebSocket
    class MockWS:
        def __init__(self, ip):
            self.client = MockClient(ip)
        async def close(self, code, reason):
            pass

    # Fill connection attempts
    for i in range(10):
        ws = MockWS(f"192.168.1.{i}")
        await ws_limiter.accept(ws)

    assert len(ws_limiter.connection_attempts) == 10

    # Add 11th client -> becomes 11 (if check is > max_clients)
    ws_new = MockWS("192.168.1.100")
    await ws_limiter.accept(ws_new)

    # Manually advance cleanup counter to force cleanup on next call
    ws_limiter.cleanup_counter = 99

    # Add 12th client -> triggers cleanup if limit is 10 and logic is consistent
    ws_new2 = MockWS("192.168.1.101")
    await ws_limiter.accept(ws_new2)

    count = len(ws_limiter.connection_attempts)
    # We want to enforce that a limit exists.
    # Ideally count should be around 10.
    # If vulnerable (no limit), count is 12.
    # If vulnerable (clear all), count is 1.

    # If prune 20% of 11 (approx 2), we expect ~9 + 1 (new) = 10.
    # Or if logic prunes AFTER adding, or checks BEFORE adding?
    # Logic:
    # 1. cleanup_counter check -> prune if len > max
    # 2. append new

    # Before call: 11 clients.
    # Call 12th:
    # cleanup -> 11 > 10 -> prune 20% of 11 = 2. Remaining 9.
    # append 12th -> total 10.

    print(f"WS Limiter Count: {count}")

    assert count <= 10, f"WebSocket limiter count {count} exceeds limit 10"
    assert count > 1, "WebSocket limiter should not clear all clients"
