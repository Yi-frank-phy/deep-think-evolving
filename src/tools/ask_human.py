"""
Human-in-the-Loop Tool: ask_human

This tool allows any LLM Agent to request input from a human expert
during the reasoning process. The tool will broadcast a request via
WebSocket and wait for the human's response.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional
from langchain_core.tools import tool

# Global reference to the HIL manager (set by server.py)
_hil_manager = None


def set_hil_manager(manager):
    """Set the global HIL manager reference."""
    global _hil_manager
    _hil_manager = manager


class HilRequest:
    """Represents a pending human-in-the-loop request."""
    
    def __init__(self, question: str, context: str, agent: str, timeout: int = 60):
        self.request_id = str(uuid.uuid4())
        self.question = question
        self.context = context
        self.agent = agent
        self.timeout = timeout
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.response_event = asyncio.Event()
        self.response: Optional[str] = None
    
    def to_dict(self):
        return {
            "request_id": self.request_id,
            "agent": self.agent,
            "question": self.question,
            "context": self.context,
            "timeout_seconds": self.timeout,
            "created_at": self.created_at
        }


class HilManager:
    """Manages human-in-the-loop requests and responses."""
    
    def __init__(self):
        self.pending_requests: dict[str, HilRequest] = {}
        self.broadcast_func = None
    
    def set_broadcast_func(self, func):
        """Set the broadcast function for sending WebSocket messages."""
        self.broadcast_func = func
    
    async def request_human_input(
        self, 
        question: str, 
        context: str = "", 
        agent: str = "unknown",
        timeout: int = 60
    ) -> str:
        """
        Send a request to the human and wait for response.
        
        Args:
            question: The question to ask the human
            context: Optional context to help the human understand
            agent: The agent making the request
            timeout: Seconds to wait for response
            
        Returns:
            Human's response or a timeout message
        """
        request = HilRequest(question, context, agent, timeout)
        self.pending_requests[request.request_id] = request
        
        # Broadcast the request to the frontend
        if self.broadcast_func:
            await self.broadcast_func({
                "type": "hil_required",
                "data": request.to_dict()
            })
            print(f"[HIL] Request sent: {request.request_id} from {agent}")
        
        try:
            # Wait for response with timeout
            await asyncio.wait_for(
                request.response_event.wait(),
                timeout=timeout
            )
            response = request.response or "[Empty response]"
            print(f"[HIL] Response received: {response[:50]}...")
            return response
            
        except asyncio.TimeoutError:
            print(f"[HIL] Request {request.request_id} timed out")
            return "[No human response within timeout - continuing autonomously]"
            
        finally:
            # Clean up
            self.pending_requests.pop(request.request_id, None)
    
    def submit_response(self, request_id: str, response: str) -> bool:
        """
        Submit a human response to a pending request.
        
        Args:
            request_id: The request ID
            response: The human's response
            
        Returns:
            True if the request was found and responded to
        """
        request = self.pending_requests.get(request_id)
        if request:
            request.response = response
            request.response_event.set()
            return True
        return False


# Global HIL manager instance
hil_manager = HilManager()


@tool
def ask_human(question: str, context: str = "") -> str:
    """
    Request input from a human expert during reasoning.
    
    Use this tool when you need human judgment, clarification, or domain expertise
    that cannot be reliably determined through reasoning alone.
    
    Examples of when to use:
    - "Should I prioritize computational efficiency or code readability here?"
    - "This strategy involves a risky assumption. Do you want me to proceed?"
    - "I found multiple valid approaches. Which direction should I explore?"
    
    Args:
        question: The specific question to ask the human. Be clear and concise.
        context: Optional additional context to help the human understand the situation.
    
    Returns:
        The human's response as a string.
    """
    # This is a synchronous wrapper - the actual async call happens in the agent
    # For now, return a placeholder that will be replaced by the async version
    return f"[HIL PLACEHOLDER: {question}]"


async def ask_human_async(question: str, context: str = "", agent: str = "unknown") -> str:
    """
    Async version of ask_human for use within agent execution.
    
    Args:
        question: The question to ask
        context: Optional context
        agent: The agent making the request
        
    Returns:
        Human's response
    """
    return await hil_manager.request_human_input(
        question=question,
        context=context,
        agent=agent,
        timeout=60
    )
