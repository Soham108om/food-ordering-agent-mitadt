import secrets
from fastapi import Request, HTTPException, status
from app.db.session_store import session_store

async def get_session_id(request: Request) -> str:
    """
    Extracts the opaque session_id from the HttpOnly cookie or X-Session-ID header.
    Generates a new session_id if none exists.
    """
    session_id = request.cookies.get("food_agent_session") or request.headers.get("X-Session-ID")
    if not session_id:
        session_id = secrets.token_urlsafe(24)
    return session_id
