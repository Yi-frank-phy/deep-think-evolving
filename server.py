"""FastAPI server exposing a WebSocket feed for knowledge base reflections."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
POLL_INTERVAL_SECONDS = 1.0

logger = logging.getLogger(__name__)


app = FastAPI(title="Prometheus Control Tower Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

from pydantic import BaseModel
from src.core.graph_builder import build_deep_think_graph
from src.core.state import DeepThinkState
from src.strategy_architect import expand_strategy_node

class ExpandNodeRequest(BaseModel):
    rationale: str
    context: str | None = None
    model_name: str = "gemini-1.5-flash"  # Default


class SimulationConfig(BaseModel):
    t_max: float = 2.0
    c_explore: float = 1.0
    beam_width: int = 3
    thinking_budget: int = 1024  # Default token budget for thinking

class SimulationRequest(BaseModel):
    problem: str
    config: SimulationConfig = SimulationConfig()

class SimulationManager:
    def __init__(self):
        self.active_websockets: List[WebSocket] = []
        self.current_task: asyncio.Task | None = None
        self.is_running = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.append(websocket)
        logger.info(f"Client connected to simulation stream. Total: {len(self.active_websockets)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_websockets:
            self.active_websockets.remove(websocket)

    async def broadcast(self, message: dict):
        for ws in self.active_websockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")

    async def run_graph(self, problem: str, config: SimulationConfig):
        self.is_running = True
        await self.broadcast({"type": "status", "data": "started"})
        
        try:
            print(f"Building graph for: {problem} with config {config}")
            graph_app = build_deep_think_graph()
            
            initial_state: DeepThinkState = {
                "problem_state": problem,
                "strategies": [],
                "research_context": None,
                "spatial_entropy": 0.0,
                "effective_temperature": 0.0,
                "normalized_temperature": 0.0,
                "config": config.dict(),
                "virtual_filesystem": {},
                "history": ["Graph initialized via Server"]
            }

            # Use astream (stream_mode="updates" gives diffs, "values" gives full state)
            # "updates" is better for bandwidth if supported, but "values" is easier to debug.
            # Let's use "values" for now to ensure we have full context.
            async for event in graph_app.astream(initial_state, stream_mode="values"):
                # Clean up event for JSON serialization (remove unserializable objects if any)
                # StrategyNode is dict, so should be fine.
                
                # Emit state update
                await self.broadcast({
                    "type": "state_update",
                    "data": event # 'event' IS the DeepThinkState dict
                })
                
                # Sleep a tiny bit to allow UI to render if loop is tight
                await asyncio.sleep(0.1)
                
            await self.broadcast({"type": "status", "data": "completed"})
            
        except Exception as e:
            logger.exception("Simulation failed")
            await self.broadcast({"type": "error", "data": str(e)})
        finally:
            self.is_running = False
            self.current_task = None

sim_manager = SimulationManager()

@app.post("/api/simulation/start")
async def start_simulation(req: SimulationRequest):
    if sim_manager.is_running:
        return {"status": "error", "message": "Simulation already running"}
    
    sim_manager.current_task = asyncio.create_task(sim_manager.run_graph(req.problem, req.config))
    return {"status": "started", "problem": req.problem}

@app.get("/api/simulation/stop")
async def stop_simulation():
    if sim_manager.current_task:
        sim_manager.current_task.cancel()
        sim_manager.is_running = False
        await sim_manager.broadcast({"type": "status", "data": "stopped"})
        return {"status": "stopped"}
    return {"status": "not_running"}

@app.post("/api/expand_node")
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
        return {"expanded_content": f"Error: {str(e)}"}


@app.websocket("/ws/simulation")
async def simulation_websocket(websocket: WebSocket):
    await sim_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, maybe listen for client commands (breakpoints?)
            data = await websocket.receive_text()
            # Echo or process
    except WebSocketDisconnect:
        sim_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS error: {e}")
        sim_manager.disconnect(websocket)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
