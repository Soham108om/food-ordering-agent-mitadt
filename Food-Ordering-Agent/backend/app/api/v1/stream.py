import json
import asyncio
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.db.session_store import session_store

router = APIRouter(prefix="/stream", tags=["Streaming"])

# Upper bound on how long a single SSE connection stays open.
STREAM_MAX_SECONDS = 300

@router.get("/{session_id}")
async def stream_agent_events(session_id: str):
    """
    Streams live AgentState updates and timeline events via Server-Sent Events (SSE).
    Every event is derived strictly from actual backend LangGraph node execution.
    """
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    async def event_generator():
        last_snapshot = None
        deadline = asyncio.get_running_loop().time() + STREAM_MAX_SECONDS
        while True:
            current_session = await session_store.get_session(session_id)
            if not current_session:
                break

            current_step = current_session.get("current_step")
            agent_state = current_session.get("agent_state") or {}
            needs_user_input = current_session.get("needs_user_input")
            replanning_required = current_session.get("replanning_required")
            snapshot = json.dumps(
                {
                    "current_step": current_step,
                    "needs_user_input": needs_user_input,
                    "replanning_required": replanning_required,
                    "state": agent_state
                },
                ensure_ascii=False,
                sort_keys=True
            )
            if snapshot != last_snapshot:
                last_snapshot = snapshot
                payload = {
                    "session_id": session_id,
                    "current_step": current_step,
                    "needs_user_input": needs_user_input,
                    "replanning_required": replanning_required,
                    "state": agent_state
                }
                yield {
                    "event": "agent_update",
                    "data": json.dumps(payload, ensure_ascii=False)
                }

            if current_step in ("END", "TRACK", "ERROR"):
                # Pause or finish streaming
                yield {
                    "event": "agent_idle",
                    "data": json.dumps({
                        "status": "error" if current_step == "ERROR" else "paused_or_completed",
                        "step": current_step
                    })
                }
                break

            await asyncio.sleep(0.5)

            # Safety net: never hold the connection open indefinitely.
            if asyncio.get_running_loop().time() > deadline:
                yield {
                    "event": "agent_idle",
                    "data": json.dumps({"status": "timeout", "step": current_step})
                }
                break

    return EventSourceResponse(event_generator())
