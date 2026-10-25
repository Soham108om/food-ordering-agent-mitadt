import base64
import hashlib
import secrets
from typing import Dict, Any
from urllib.parse import urlencode
import requests

from app.core.config import settings

def generate_pkce_credentials() -> Dict[str, str]:
    """
    Generates PKCE verifier, challenge (S256), and CSRF state token.
    """
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).decode().rstrip("=")
    state = secrets.token_urlsafe(32)

    return {
        "code_verifier": code_verifier,
        "code_challenge": code_challenge,
        "state": state
    }

def register_swiggy_oauth_client(redirect_uri: str = settings.REDIRECT_URI) -> str:
    """
    Registers dynamic OAuth client with Swiggy auth server. Returns client_id.
    """
    registration_payload = {
        "client_name": "Food Ordering Agent - Production Web App",
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none"
    }

    response = requests.post(
        f"{settings.AUTH_BASE}/auth/register",
        json=registration_payload,
        timeout=30
    )
    response.raise_for_status()
    client_data = response.json()
    return client_data["client_id"]

def build_authorization_url(client_id: str, code_challenge: str, state: str, redirect_uri: str = settings.REDIRECT_URI) -> str:
    """
    Constructs the Swiggy OAuth authorization URL.
    """
    authorization_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "scope": settings.SCOPE,
    }
    return f"{settings.AUTH_BASE}/auth/authorize?" + urlencode(authorization_params)

def exchange_code_for_token(code: str, code_verifier: str, client_id: str, redirect_uri: str = settings.REDIRECT_URI) -> Dict[str, Any]:
    """
    Exchanges authorization code for Swiggy access token.
    """
    token_url = f"{settings.AUTH_BASE}/auth/token"
    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }

    response = requests.post(token_url, data=token_payload, timeout=30)
    response.raise_for_status()
    return response.json()
