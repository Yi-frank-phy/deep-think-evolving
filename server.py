"""FastAPI server exposing a WebSocket feed for knowledge base reflections."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
