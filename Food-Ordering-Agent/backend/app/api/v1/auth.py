from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from app.api.deps import get_session_id
from app.db.session_store import session_store
from app.mcp.oauth import (
    generate_pkce_credentials,
    register_swiggy_oauth_client,
    build_authorization_url,
    exchange_code_for_token
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["OAuth"])

@router.get("/login")
async def swiggy_login(response: Response, session_id: str = Depends(get_session_id)):
    """
    Initiates Swiggy OAuth PKCE flow.
    Registers client dynamically, generates PKCE, stores verifier in SQLite session,
    sets HttpOnly session cookie, and returns Swiggy authorization URL.
    """
    pkce = generate_pkce_credentials()
    client_id = register_swiggy_oauth_client(settings.REDIRECT_URI)
    auth_url = build_authorization_url(client_id, pkce["code_challenge"], pkce["state"], settings.REDIRECT_URI)

    # Save PKCE parameters into persistent session store
    await session_store.create_session(
        session_id=session_id,
        pkce_code_verifier=pkce["code_verifier"],
        oauth_state=pkce["state"]
    )

    # Set HttpOnly session cookie (never exposing raw tokens to JS)
    response.set_cookie(
        key="food_agent_session",
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE
    )

    return {
        "status": "ok",
        "authorization_url": auth_url,
        "session_id": session_id,
        "client_id": client_id
    }

@router.get("/callback")
async def swiggy_callback(code: str, state: str, session_id: str = Depends(get_session_id)):
    """
    Swiggy OAuth callback endpoint.
    Exchanges code for Swiggy access token using PKCE verifier stored in backend session.
    Encrypts token and saves to SQLite.
    """
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="OAuth session expired or invalid.")

    if session.get("oauth_state") and session.get("oauth_state") != state:
        raise HTTPException(status_code=400, detail="OAuth state mismatch CSRF validation failed.")

    code_verifier = session.get("pkce_code_verifier")
    if not code_verifier:
        raise HTTPException(status_code=400, detail="PKCE verifier missing from session.")

    # Re-register client ID or use standard client context
    client_id = register_swiggy_oauth_client(settings.REDIRECT_URI)

    try:
        token_data = exchange_code_for_token(
            code=code,
            code_verifier=code_verifier,
            client_id=client_id,
            redirect_uri=settings.REDIRECT_URI
        )
        access_token = token_data["access_token"]
        await session_store.save_swiggy_token(session_id, access_token)

        # Redirect to frontend dashboard or return success
        return {
            "status": "authenticated",
            "message": "Swiggy OAuth successful. Access token encrypted and saved server-side.",
            "expires_in": token_data.get("expires_in")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to exchange authorization code: {str(e)}")

@router.get("/status")
async def swiggy_status(session_id: str = Depends(get_session_id)):
    """
    Returns Swiggy authentication status for current session.
    """
    token = await session_store.get_swiggy_token(session_id)
    return {
        "session_id": session_id,
        "authenticated": bool(token)
    }
