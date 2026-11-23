import json
import asyncio
from typing import Dict, Any, Optional
from app.db.session_store import session_store, safe_json_dumps

# The server's event loop. LangGraph executes *synchronous* nodes inside a
# worker thread (no running event loop there), so those nodes cannot call
# `loop.create_task()` directly. We register the main loop once per graph run
# so sync nodes can hand their DB write back to it via `run_coroutine_threadsafe`.
_main_loop: Optional[asyncio.AbstractEventLoop] = None


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Registers the server's event loop for cross-thread state persistence."""
    global _main_loop
    _main_loop = loop


def sanitize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Converts state to clean JSON-serializable structure without raw tokens."""
    state_copy = dict(state)
    if "swiggy_access_token" in state_copy:
        del state_copy["swiggy_access_token"]
    return json.loads(safe_json_dumps(state_copy))


def notify_state_update(state: Dict[str, Any]):
    """Helper to emit live state updates to SQLite session store per node execution."""
    session_id = state.get("session_id")
    if not session_id:
        return

    clean = sanitize_state(state)
    coro = session_store.update_agent_state(
        session_id=session_id,
        agent_state=clean,
        current_step=clean.get("current_step"),
        needs_user_input=clean.get("needs_user_input"),
        replanning_required=clean.get("replanning_required")
    )

    # Async nodes run on the event loop itself -> schedule directly.
    try:
        asyncio.get_running_loop().create_task(coro)
        return
    except RuntimeError:
        pass

    # Sync nodes run in a LangGraph worker thread -> hop back to the main loop.
    if _main_loop is not None and not _main_loop.is_closed():
        asyncio.run_coroutine_threadsafe(coro, _main_loop)
    else:
        coro.close()
