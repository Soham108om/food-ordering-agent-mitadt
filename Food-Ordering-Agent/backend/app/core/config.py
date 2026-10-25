import os
import base64
import hashlib
from dotenv import load_dotenv
from pydantic import BaseModel

# Load .env if present
load_dotenv()

class Settings(BaseModel):
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    SWIGGY_MCP_URL: str = os.environ.get("SWIGGY_MCP_URL", "https://mcp.swiggy.com/food")
    AUTH_BASE: str = os.environ.get("AUTH_BASE", "https://mcp.swiggy.com")
    REDIRECT_URI: str = os.environ.get(
        "SWIGGY_REDIRECT_URI",
        os.environ.get("REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback")
    )
    SCOPE: str = os.environ.get("SCOPE", "mcp:tools")
    DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "food_agent_sessions.db")
    SESSION_ENCRYPTION_KEY: str = os.environ.get("SESSION_ENCRYPTION_KEY", "")
    FRONTEND_ORIGIN: str = os.environ.get("FRONTEND_ORIGIN", "")
    COOKIE_SECURE: bool = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

    def get_fernet_key(self) -> bytes:
        raw_key = self.SESSION_ENCRYPTION_KEY or os.environ.get("SECRET_KEY", "food_ordering_agent_secure_salt_key_2026")
        digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

settings = Settings()
