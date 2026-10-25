import json
import asyncio
from typing import Dict, Any
from app.db.session_store import session_store, safe_json_dumps

def sanitize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Converts state to clean JSON-serializable structure without raw tokens."""
    state_copy = dict(state)
    if "swiggy_access_token" in state_copy:
        del state_copy["swiggy_access_token"]
    return json.loads(safe_json_dumps(state_copy))

def notify_state_update(state: Dict[str, Any]):
    """Helper to emit live state updates to SQLite session store per node execution."""
    session_id = state.get("session_id")
    if session_id:
        clean = sanitize_state(state)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                session_store.update_agent_state(
                    session_id=session_id,
                    agent_state=clean,
                    current_step=clean.get("current_step"),
                    needs_user_input=clean.get("needs_user_input"),
                    replanning_required=clean.get("replanning_required")
                )
            )
        except RuntimeError:
            pass
