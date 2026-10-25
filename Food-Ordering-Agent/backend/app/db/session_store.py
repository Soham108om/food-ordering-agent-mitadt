import json
import sqlite3
import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.core.security import encrypt_token, decrypt_token

def safe_json_serializer(obj: Any) -> Any:
    """
    Custom JSON serializer for MCP TextContent, Pydantic models, and custom objects.
    Prevents TypeError during state persistence.
    """
    if hasattr(obj, "dict") and callable(obj.dict):
        return obj.dict()
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)

def safe_json_dumps(data: Any, indent: Optional[int] = None) -> str:
    return json.dumps(data, default=safe_json_serializer, indent=indent, ensure_ascii=False)

class SessionStore:
    def __init__(self, db_path: str = settings.DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initializes SQLite database schema asynchronously."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    encrypted_swiggy_token TEXT,
                    pkce_code_verifier TEXT,
                    oauth_state TEXT,
                    agent_state_json TEXT,
                    current_step TEXT,
                    needs_user_input INTEGER DEFAULT 0,
                    replanning_required INTEGER DEFAULT 0,
                    events_log_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            await db.commit()

    async def create_session(self, session_id: str, pkce_code_verifier: Optional[str] = None, oauth_state: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO sessions 
                (session_id, encrypted_swiggy_token, pkce_code_verifier, oauth_state, agent_state_json, current_step, needs_user_input, replanning_required, events_log_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, "", pkce_code_verifier or "", oauth_state or "", safe_json_dumps({}), "INIT", 0, 0, safe_json_dumps([]), now, now)
            )
            await db.commit()
        return await self.get_session(session_id)

    async def save_swiggy_token(self, session_id: str, swiggy_access_token: str):
        encrypted = encrypt_token(swiggy_access_token)
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET encrypted_swiggy_token = ?, updated_at = ? WHERE session_id = ?",
                (encrypted, now, session_id)
            )
            await db.commit()

    async def get_swiggy_token(self, session_id: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT encrypted_swiggy_token FROM sessions WHERE session_id = ?", (session_id,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    return decrypt_token(row[0])
        return None

    async def update_agent_state(
        self,
        session_id: str,
        agent_state: Dict[str, Any],
        current_step: Optional[str] = None,
        needs_user_input: Optional[bool] = None,
        replanning_required: Optional[bool] = None,
        event_entry: Optional[Dict[str, Any]] = None
    ):
        session = await self.get_session(session_id)
        if not session:
            await self.create_session(session_id)
            session = await self.get_session(session_id)

        events_log = session.get("events_log", [])
        if event_entry:
            events_log.append(event_entry)

        now = datetime.utcnow().isoformat()
        step = current_step if current_step is not None else agent_state.get("current_step", "UNKNOWN")
        needs_input = int(needs_user_input if needs_user_input is not None else agent_state.get("needs_user_input", False))
        replan_req = int(replanning_required if replanning_required is not None else agent_state.get("replanning_required", False))

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE sessions 
                SET agent_state_json = ?, current_step = ?, needs_user_input = ?, replanning_required = ?, events_log_json = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (safe_json_dumps(agent_state), step, needs_input, replan_req, safe_json_dumps(events_log), now, session_id)
            )
            await db.commit()

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                data = dict(row)
                token = decrypt_token(data.get("encrypted_swiggy_token", "")) if data.get("encrypted_swiggy_token") else None
                return {
                    "session_id": data["session_id"],
                    "swiggy_access_token": token,
                    "pkce_code_verifier": data.get("pkce_code_verifier"),
                    "oauth_state": data.get("oauth_state"),
                    "agent_state": json.loads(data.get("agent_state_json") or "{}"),
                    "current_step": data.get("current_step"),
                    "needs_user_input": bool(data.get("needs_user_input")),
                    "replanning_required": bool(data.get("replanning_required")),
                    "events_log": json.loads(data.get("events_log_json") or "[]"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at")
                }

session_store = SessionStore()
