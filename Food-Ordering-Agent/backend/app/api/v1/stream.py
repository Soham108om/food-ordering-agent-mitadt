import json
import asyncio
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.db.session_store import session_store

router = APIRouter(prefix="/stream", tags=["Streaming"])

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
        last_step = None
        while True:
            current_session = await session_store.get_session(session_id)
            if not current_session:
                break

            current_step = current_session.get("current_step")
            if current_step != last_step:
                last_step = current_step
                payload = {
                    "session_id": session_id,
                    "current_step": current_step,
                    "needs_user_input": current_session.get("needs_user_input"),
                    "replanning_required": current_session.get("replanning_required"),
                    "state": current_session.get("agent_state")
                }
                yield {
                    "event": "agent_update",
                    "data": json.dumps(payload, ensure_ascii=False)
                }

            if current_step in ("END", "TRACK") or current_session.get("needs_user_input"):
                # Pause or finish streaming
                yield {
                    "event": "agent_idle",
                    "data": json.dumps({"status": "paused_or_completed", "step": current_step})
                }
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
