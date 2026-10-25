import sys
# Configure UTF-8 encoding for stdout/stderr to prevent Windows cp1252 UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session_store import session_store
from app.api.v1.auth import router as auth_router
from app.api.v1.agent import router as agent_router
from app.api.v1.stream import router as stream_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize persistent DB schema
    await session_store.init_db()
    print("✓ Persistent SQLite session store initialized")
    yield

app = FastAPI(
    title="Food Ordering Agent API",
    description="Real agent backend powered by Gemini + LangGraph + Swiggy MCP",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local development & production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(stream_router, prefix="/api/v1")

@app.get("/")
async def root_health():
    return {
        "status": "online",
        "service": "Food Ordering Agent Backend API",
        "mcp_url": settings.SWIGGY_MCP_URL,
        "redirect_uri": settings.REDIRECT_URI
    }
