"""FastAPI server exposing a WebSocket feed for knowledge base reflections."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
import time
from collections import defaultdict

import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import webbrowser
import sys

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
POLL_INTERVAL_SECONDS = 1.0

logger = logging.getLogger(__name__)

# Standard generic error message to prevent information leakage
GENERIC_ERROR_MESSAGE = "An internal error occurred. Please check the server logs."

# Security: Rate Limiting
class SimpleRateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_counts = defaultdict(list)

    async def __call__(self, request: Request):
        # Identify client by IP
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean up old timestamps (older than 1 minute)
        self.request_counts[client_ip] = [
            t for t in self.request_counts[client_ip]
            if now - t < 60
        ]

        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

        self.request_counts[client_ip].append(now)

# Create rate limiter instance (60 requests/min)
rate_limiter = SimpleRateLimiter(requests_per_minute=60)

app = FastAPI(title="Prometheus Control Tower Backend", version="0.1.0")

# Security: Add security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Content Security Policy (CSP)
    # Allows scripts/styles from self and inline (required for React/Vite)
    # Allows WebSockets for real-time updates
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "connect-src 'self' ws: wss:; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:;"
    )
    response.headers["Content-Security-Policy"] = csp_policy
    return response

# Security: Restrict CORS to allowed origins
# When allow_credentials=True, allow_origins cannot be ["*"]
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS")
if allowed_origins_env:
    allow_origins = allowed_origins_env.split(",")
else:
    # Default to local development ports
    allow_origins = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Available Gemini models - Gemini 3.0 series with thinking_level support
# Model IDs from https://ai.google.dev/gemini-api/docs/models
# thinking_levels: MINIMAL (Flash only), LOW, MEDIUM (Flash only), HIGH
AVAILABLE_MODELS = [
    # Default - affordable with good performance
    {"id": "gemini-2.5-flash-lite-preview-06-17", "name": "⚡ 2.5 Flash-Lite", "thinking_levels": ["LOW", "HIGH"], "tier": "free"},
    # Gemini 3.0 Flash - supports all levels including MINIMAL and MEDIUM
    {"id": "gemini-3.0-flash-preview", "name": "🔥 3.0 Flash", "thinking_levels": ["MINIMAL", "LOW", "MEDIUM", "HIGH"], "tier": "standard"},
    # Gemini 3.0 Pro - supports LOW and HIGH only
    {"id": "gemini-3.0-pro-preview", "name": "💎 3.0 Pro", "thinking_levels": ["LOW", "HIGH"], "tier": "premium"},
]


def _collect_reflection_payload(path: Path) -> Dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {}

    embedding = payload.get("embedding") or []
    created_at = payload.get("created_at")
    if not created_at:
        created_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()

    return {
        "id": payload.get("id", path.stem),
        "thread_id": payload.get("thread_label") or payload.get("thread_id") or path.stem,
        "outcome": payload.get("outcome", "unknown"),
        "created_at": created_at,
        "reflection": payload.get("reflection", ""),
        "embedding_dimensions": len(embedding),
        "embedding_preview": embedding[:8],
    }


def _list_reflection_files() -> List[Path]:
    return sorted(KNOWLEDGE_BASE_DIR.glob("*.json"))


@app.get("/health", tags=["meta"])
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/models", tags=["config"], dependencies=[Depends(rate_limiter)])
async def get_available_models():
    """Returns available models with their thinking budget constraints."""
    return {"models": AVAILABLE_MODELS}


@app.websocket("/ws/knowledge_base")
async def knowledge_base_updates(websocket: WebSocket) -> None:
    await websocket.accept()

    reflection_files = _list_reflection_files()
    snapshot = [_collect_reflection_payload(path) for path in reflection_files]
    await websocket.send_json({"type": "snapshot", "data": snapshot})

    last_seen: Dict[str, float] = {path.stem: path.stat().st_mtime for path in reflection_files}

    try:
        while True:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

            current_files = _list_reflection_files()
            current_ids = {path.stem for path in current_files}

            # Detect deletions
            removed_ids = set(last_seen.keys()) - current_ids
            for thread_id in removed_ids:
                await websocket.send_json({"type": "delete", "data": {"id": thread_id}})
                last_seen.pop(thread_id, None)

            # Detect new or updated files
            for path in current_files:
                modified = path.stat().st_mtime
                if last_seen.get(path.stem) != modified:
                    payload = _collect_reflection_payload(path)
                    await websocket.send_json({"type": "update", "data": payload})
                    last_seen[path.stem] = modified

    except WebSocketDisconnect:
        return
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Knowledge base websocket crashed", exc_info=exc)
        await websocket.close(code=1011)


# --- Simulation Control & Telemetry ---

import base64
from pydantic import BaseModel, Field, field_validator
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from src.core.graph_builder import build_deep_think_graph
from src.core.state import DeepThinkState
from src.strategy_architect import expand_strategy_node
from src.tools.ask_human import hil_manager

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=50000, description="User message limited to 50k chars")
    instruction: str | None = Field(None, max_length=10000, description="Optional system instruction")
    audio_base64: str | None = Field(None, max_length=15_000_000, description="Optional audio input limited to ~11MB")
    model_name: str = "gemini-2.5-flash"

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        valid_ids = {m["id"] for m in AVAILABLE_MODELS}
        if v not in valid_ids:
            # Fallback for older clients or if model removed, but log warning?
            # Enforcing strict validation for security.
            raise ValueError(f"Invalid model name: {v}. Must be one of {valid_ids}")
        return v

class ExpandNodeRequest(BaseModel):
    rationale: str = Field(..., max_length=50000, description="Strategy rationale limited to 50k chars")
    context: str | None = Field(None, max_length=1_000_000, description="Optional context limited to 1M chars")
    model_name: str = "gemini-2.5-flash"  # Default


class SimulationConfig(BaseModel):
    model_name: str = "gemini-2.5-flash-lite-preview-06-17"  # Default model
    t_max: float = 2.0
    c_explore: float = 1.0
    beam_width: int = 3
    thinking_level: str = "HIGH"  # Thinking depth: MINIMAL, LOW, MEDIUM, HIGH
    # --- Added to sync with frontend ---
    max_iterations: int = 10  # Maximum evolution iterations before forced termination
    entropy_change_threshold: float = 0.01  # Lower threshold for high-dim embeddings
    total_child_budget: int = 6  # Total children to allocate across strategies
    # NOTE: LLM temperature is always 1.0 (Logic Manifold Integrity)
    # System temperature τ controls resource allocation only (see temperature_helper.py)

class SimulationRequest(BaseModel):
    problem: str = Field(..., max_length=50000, description="Problem description limited to 50k chars")
    config: SimulationConfig = SimulationConfig()

class HilResponse(BaseModel):
    request_id: str
    response: str = Field(..., max_length=50000, description="Human response limited to 50k chars")

class SimulationManager:
    def __init__(self):
        self.active_websockets: List[WebSocket] = []
        self.current_task: asyncio.Task | None = None
        self.is_running = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.append(websocket)
        # Set up HIL manager to use our broadcast function
        hil_manager.set_broadcast_func(self.broadcast)
        logger.info(f"Client connected to simulation stream. Total: {len(self.active_websockets)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_websockets:
            self.active_websockets.remove(websocket)

    async def broadcast(self, message: dict):
        if not self.active_websockets:
            return

        # Optimization: Send to all clients in parallel to reduce latency
        async def send_safe(ws):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")

        await asyncio.gather(*(send_safe(ws) for ws in self.active_websockets))

    async def run_graph(self, problem: str, config: SimulationConfig):
        self.is_running = True
        await self.broadcast({"type": "status", "data": "started"})
        
        try:
            print(f"Building graph for: {problem} with config {config}")
            graph_app = build_deep_think_graph()
            
            initial_state: DeepThinkState = {
                "problem_state": problem,
                "subtasks": [],
                "information_needs": [],
                "strategies": [],
                "research_context": None,
                "research_status": "insufficient",
                "spatial_entropy": 0.0,
                "effective_temperature": 0.0,
                "normalized_temperature": 0.0,
                "config": config.model_dump(),  # Use model_dump instead of dict()
                "virtual_filesystem": {},
                "history": ["Graph initialized via Server"],
                "iteration_count": 0,
                "research_iteration": 0,
                "judge_context": None,
                "architect_decisions": []
            }

            # Broadcast initial state so frontend has a baseline
            await self.broadcast({
                "type": "state_update",
                "data": initial_state
            })

            # Agent display names for UI - synced with types.ts AgentPhase
            agent_names = {
                "task_decomposer": "📋 Task Decomposer",
                "researcher": "🔍 Researcher",
                "strategy_generator": "💡 Strategy Generator",
                "distiller": "📝 Distiller",
                "architect": "🏗️ Architect",
                "architect_scheduler": "📅 Scheduler",
                "distiller_for_judge": "📋 Context Prep",
                "executor": "⚙️ Executor",
                "judge": "⚖️ Judge",
                "evolution": "🧬 Evolution",
                "propagation": "🌱 Propagation"
                # Note: writer removed - report generation is now dynamically handled by Executor
            }
            
            current_agent = None

            # Use astream with stream_mode="updates" - returns dict {node_name: output}
            # Set recursion_limit high enough to allow for research loops and evolution loops
            run_config = {"recursion_limit": 100}  # Allow up to 100 recursive calls
            async for chunk in graph_app.astream(initial_state, stream_mode="updates", config=run_config):
                # chunk is a dict like {"node_name": node_output}
                for node_name, node_output in chunk.items():
                    print(f"[Stream] Node: {node_name}")
                    
                    # Determine the agent from node name
                    agent_key = node_name if node_name in agent_names else None
                    
                    if agent_key and agent_key != current_agent:
                        # Send agent start notification
                        current_agent = agent_key
                        await self.broadcast({
                            "type": "agent_start",
                            "data": {
                                "agent": agent_key,
                                "message": f"{agent_names[agent_key]} 开始处理..."
                            }
                        })
                        await asyncio.sleep(0.05)
                    
                    # Broadcast state update if we have valid state
                    if isinstance(node_output, dict):
                        # Get latest progress detail from the delta
                        # Since we use stream_mode="updates", node_output["history"] is just the new items
                        history_update = node_output.get("history", [])
                        detail = history_update[-1] if history_update else None
                        
                        # Send state update
                        await self.broadcast({
                            "type": "state_update",
                            "data": node_output
                        })
                        
                        if agent_key:
                            # Send progress update with summary
                            await self.broadcast({
                                "type": "agent_progress",
                                "data": {
                                    "agent": agent_key,
                                    "message": f"{agent_names[agent_key]} 处理中",
                                    "detail": detail
                                }
                            })
                    
                    # Small delay for UI rendering
                    await asyncio.sleep(0.05)
            
            # Send final complete for last agent
            if current_agent:
                await self.broadcast({
                    "type": "agent_complete",
                    "data": {
                        "agent": current_agent,
                        "message": f"{agent_names.get(current_agent, current_agent)} 已完成"
                    }
                })
                
            await self.broadcast({"type": "status", "data": "completed"})
            
            # Broadcast final report if available
            # Get final state from the last chunk (node_output contains the delta)
            # We need to get final_report from node_output after writer runs
            # The last node_output should have final_report if writer ran
            if 'final_report' in node_output:
                await self.broadcast({
                    "type": "final_report",
                    "data": node_output["final_report"]
                })
            
        except Exception as e:
            logger.exception("Simulation failed")
            await self.broadcast({"type": "error", "data": GENERIC_ERROR_MESSAGE})
        finally:
            self.is_running = False
            self.current_task = None

sim_manager = SimulationManager()

@app.post("/api/simulation/start", dependencies=[Depends(rate_limiter)])
async def start_simulation(req: SimulationRequest):
    if sim_manager.is_running:
        return {"status": "error", "message": "Simulation already running"}
    
    sim_manager.current_task = asyncio.create_task(sim_manager.run_graph(req.problem, req.config))
    return {"status": "started", "problem": req.problem}

@app.get("/api/simulation/stop", dependencies=[Depends(rate_limiter)])
async def stop_simulation():
    if sim_manager.current_task:
        sim_manager.current_task.cancel()
        sim_manager.is_running = False
        await sim_manager.broadcast({"type": "status", "data": "stopped"})
        return {"status": "stopped"}
    return {"status": "not_running"}

@app.post("/api/expand_node", dependencies=[Depends(rate_limiter)])
async def expand_node_endpoint(req: ExpandNodeRequest):
    """
    Stateless endpoint to expand a node's rationale.
    """
    try:
        # Pydantic validates the request body against ExpandNodeRequest
        content = expand_strategy_node(
            rationale=req.rationale,
            context=req.context,
            model_name=req.model_name
        )
        return {"expanded_content": content}
    except Exception as e:
        logger.error(f"Error in expand_node_endpoint: {e}")
        return {"expanded_content": GENERIC_ERROR_MESSAGE}


@app.websocket("/ws/simulation")
async def simulation_websocket(websocket: WebSocket):
    await sim_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for client commands (breakpoints?)
            _ = await websocket.receive_text()
            # Echo or process
    except WebSocketDisconnect:
        sim_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS error: {e}")
        sim_manager.disconnect(websocket)


@app.post("/api/chat/stream", dependencies=[Depends(rate_limiter)])
async def chat_stream_endpoint(req: ChatRequest):
    """
    Streaming chat endpoint that supports text and audio input.
    Returns Server-Sent Events (SSE) for real-time streaming.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        async def error_gen():
            yield f"data: {json.dumps({'error': 'GEMINI_API_KEY not set'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")
    
    async def generate():
        try:
            client = genai.Client(api_key=api_key)
            
            # Build content parts
            contents = []
            
            # Add instruction as system context if provided
            if req.instruction:
                contents.append(f"[System Instruction]: {req.instruction}\n\n")
            
            # Add audio part if provided
            if req.audio_base64:
                try:
                    audio_bytes = base64.b64decode(req.audio_base64)
                    audio_part = types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type="audio/webm"
                    )
                    contents.append(audio_part)
                except Exception as audio_err:
                    yield f"data: {json.dumps({'error': f'Audio decode error: {str(audio_err)}'})}\n\n"
                    return
            
            # Add message text
            contents.append(req.message)
            
            # Configure generation
            config = types.GenerateContentConfig(
                temperature=1.0,  # Logic Manifold Integrity
            )
            
            # Stream response
            response = client.models.generate_content_stream(
                model=req.model_name,
                contents=contents,
                config=config,
            )
            
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"data: {json.dumps({'error': GENERIC_ERROR_MESSAGE})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# --- Human-in-the-Loop API ---

@app.post("/api/hil/response", tags=["hil"], dependencies=[Depends(rate_limiter)])
async def submit_hil_response(response: HilResponse):
    """Submit a human response to a pending HIL request."""
    success = hil_manager.submit_response(response.request_id, response.response)
    if success:
        return {"status": "ok", "message": "Response submitted"}
    else:
        return {"status": "error", "message": "Request not found or already expired"}


@app.get("/api/hil/pending", tags=["hil"])
async def get_pending_hil_requests():
    """Get all pending HIL requests."""
    return {
        "pending": [req.to_dict() for req in hil_manager.pending_requests.values()]
    }


class ForceSynthesizeRequest(BaseModel):
    """Request to force synthesize selected strategies into a report."""
    strategy_ids: List[str] = Field(..., min_length=1, max_length=100, description="List of strategy IDs to synthesize (max 100)")


@app.post("/api/hil/force_synthesize", tags=["hil"], dependencies=[Depends(rate_limiter)])
async def force_synthesize_strategies(req: ForceSynthesizeRequest):
    """
    Force synthesize selected strategies into a report (HIL action).
    This triggers the Executor to generate a synthesis report and marks the selected strategies as pruned_synthesized.
    """
    if not sim_manager.is_running:
        return {"status": "error", "message": "No simulation is currently running"}
    
    if not req.strategy_ids:
        return {"status": "error", "message": "No strategies selected for synthesis"}
    
    # Broadcast the force synthesize command to the simulation
    await sim_manager.broadcast({
        "type": "HIL_FORCE_SYNTHESIZE",
        "data": {
            "strategy_ids": req.strategy_ids,
            "message": f"User requested force synthesis of {len(req.strategy_ids)} strategies"
        }
    })
    
    logger.info(f"[HIL] Force synthesize requested for strategies: {req.strategy_ids}")
    
    return {
        "status": "ok",
        "message": f"Force synthesis triggered for {len(req.strategy_ids)} strategies",
        "strategy_ids": req.strategy_ids
    }



# ============ Static File Serving (for packaged EXE) ============
# Check if running as bundled executable (PyInstaller) or if dist/ exists
DIST_DIR = BASE_DIR / "dist"
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle - dist is bundled
    DIST_DIR = Path(sys._MEIPASS) / "dist"

if DIST_DIR.exists():
    # Mount static files for production/bundled mode
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
    
    @app.get("/")
    async def serve_index():
        return FileResponse(DIST_DIR / "index.html")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # SPA fallback: serve index.html for all non-API routes
        file_path = (DIST_DIR / full_path).resolve()

        # Security: Prevent path traversal
        try:
            # Ensure the resolved path is within the DIST_DIR
            file_path.relative_to(DIST_DIR.resolve())

            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
        except ValueError:
            # Path is outside DIST_DIR
            logger.warning(f"Path traversal attempt detected: {full_path}")

        return FileResponse(DIST_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    
    # Auto-open browser for bundled EXE
    if getattr(sys, 'frozen', False) or DIST_DIR.exists():
        webbrowser.open("http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
