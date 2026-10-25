import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.api.deps import get_session_id
from app.db.session_store import session_store, safe_json_dumps
from app.mcp.client import invoke_mcp
from app.mcp.parsers import extract_first_id, extract_text
from app.agent.graph import food_agent
from app.agent.state import AgentState
from app.agent.nodes.utils import sanitize_state

router = APIRouter(prefix="/agent", tags=["Agent"])

class StartAgentRequest(BaseModel):
    user_request: str
    selected_address_id: Optional[str] = None

class RespondAgentRequest(BaseModel):
    payment_method: Optional[str] = None
    relaxed_constraints: Optional[Dict[str, Any]] = None

class ConfirmOrderRequest(BaseModel):
    user_confirmation: bool = True
    payment_method: str = "COD"

# Terminal/Waiting steps where an agent execution graph is NOT actively running in background
IDLE_OR_WAITING_STEPS = {
    "INIT", "START", "END", "TRACK", "ERROR", "PAYMENT", "CONFIRM_ORDER", "REPLAN", None
}

async def run_agent_background_task(session_id: str, state: AgentState):
    """Executes the LangGraph workflow asynchronously in the background."""
    try:
        final_state = await food_agent.ainvoke(state)
        clean_state = sanitize_state(final_state)

        await session_store.update_agent_state(
            session_id=session_id,
            agent_state=clean_state,
            current_step=clean_state.get("current_step"),
            needs_user_input=clean_state.get("needs_user_input"),
            replanning_required=clean_state.get("replanning_required")
        )
    except Exception as e:
        print("❌ Background agent execution error:", e)
        state["error_message"] = str(e)
        state["current_step"] = "ERROR"
        clean_state = sanitize_state(state)
        await session_store.update_agent_state(
            session_id=session_id,
            agent_state=clean_state,
            current_step="ERROR"
        )

@router.get("/addresses")
async def get_swiggy_addresses(session_id: str = Depends(get_session_id)):
    """
    Fetches real saved delivery addresses from Swiggy via MCP get_addresses tool.
    """
    token = await session_store.get_swiggy_token(session_id)
    if not token:
        raise HTTPException(status_code=401, detail="Swiggy authentication required.")

    try:
        raw_addresses = await invoke_mcp("get_addresses", {}, swiggy_access_token=token)
        text_addresses = extract_text(raw_addresses)
        first_address_id = extract_first_id(raw_addresses)

        return {
            "status": "ok",
            "raw_response": json.loads(safe_json_dumps(raw_addresses)),
            "formatted_text": text_addresses,
            "first_address_id": first_address_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve Swiggy addresses: {str(e)}")

@router.post("/start")
async def start_agent_workflow(
    payload: StartAgentRequest,
    session_id: str = Depends(get_session_id)
):
    """
    Triggers the real LangGraph execution workflow asynchronously.
    Resets state cleanly for new requests while preserving Swiggy OAuth token.
    Blocks duplicate concurrent executions if an active task is actively running.
    """
    token = await session_store.get_swiggy_token(session_id)
    if not token:
        raise HTTPException(status_code=401, detail="Swiggy authentication required. Please connect your Swiggy account.")

    existing_session = await session_store.get_session(session_id)
    if existing_session:
        step = existing_session.get("current_step")
        needs_input = existing_session.get("needs_user_input")

        # Concurrency Protection: If graph is actively executing in background (not idle/waiting and needs_user_input is False)
        if step not in IDLE_OR_WAITING_STEPS and not needs_input:
            print(f"⚠️ Duplicate agent start request blocked for active running session {session_id} at step {step}")
            return {
                "session_id": session_id,
                "status": "already_running",
                "current_step": step,
                "state": existing_session.get("agent_state")
            }

    address_id = payload.selected_address_id
    if not address_id:
        try:
            addr_res = await get_swiggy_addresses(session_id)
            address_id = addr_res.get("first_address_id")
        except Exception:
            address_id = None

    if not address_id:
        raise HTTPException(status_code=400, detail="No delivery address available in your Swiggy account.")

    # Fresh state initialization for NEW request while preserving OAuth token and Address
    initial_state = AgentState(
        session_id=session_id,
        swiggy_access_token=token,
        user_request=payload.user_request,
        selected_address_id=address_id,
        requirements={},
        cuisine=None,
        food_components=[],
        restaurants=[],
        parsed_restaurants=[],
        filtered_restaurants=[],
        ranked_restaurants=[],
        selected_restaurant={},
        selected_restaurant_id=None,
        menu_result=[],
        menu_options=[],
        filtered_menu_items=[],
        ranked_menu_items=[],
        selected_item={},
        customization_result=None,
        selected_customization={},
        cart_result=None,
        cart=None,
        payment_options=None,
        payment_method=None,
        user_confirmation=False,
        order_result=None,
        order_id=None,
        order_status=None,
        tracking_result=None,
        current_step="START",
        needs_user_input=False,
        replanning_required=False,
        error_message=None
    )

    clean_initial = sanitize_state(initial_state)
    await session_store.update_agent_state(
        session_id=session_id,
        agent_state=clean_initial,
        current_step="START",
        needs_user_input=False,
        replanning_required=False
    )

    # Launch new graph execution task in background
    asyncio.create_task(run_agent_background_task(session_id, initial_state))

    return {
        "session_id": session_id,
        "status": "started",
        "current_step": "START",
        "state": clean_initial
    }

@router.get("/state/{session_id}")
async def get_agent_state(session_id: str):
    """
    Retrieves full current agent execution state for a session.
    """
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    return session

@router.post("/respond")
async def respond_to_agent(
    payload: RespondAgentRequest,
    session_id: str = Depends(get_session_id)
):
    """
    Submits user choice to resume paused LangGraph execution (e.g. payment selection, constraint relaxation).
    """
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    token = await session_store.get_swiggy_token(session_id)
    if not token:
        raise HTTPException(status_code=401, detail="Swiggy authentication required.")

    current_state = session["agent_state"]
    current_state["session_id"] = session_id
    current_state["swiggy_access_token"] = token
    current_state["needs_user_input"] = False

    if payload.payment_method:
        current_state["payment_method"] = payload.payment_method

    if payload.relaxed_constraints:
        requirements = current_state.get("requirements", {})
        requirements.update(payload.relaxed_constraints)
        current_state["requirements"] = requirements
        current_state["replanning_required"] = False

    clean_state = sanitize_state(current_state)
    await session_store.update_agent_state(
        session_id=session_id,
        agent_state=clean_state,
        current_step=clean_state.get("current_step", "RESUMING"),
        needs_user_input=False
    )

    # Launch graph task in background
    asyncio.create_task(run_agent_background_task(session_id, current_state))

    return {
        "session_id": session_id,
        "status": "resumed",
        "current_step": clean_state.get("current_step"),
        "state": clean_state
    }

@router.post("/confirm")
async def confirm_and_place_order(
    payload: ConfirmOrderRequest,
    session_id: str = Depends(get_session_id)
):
    """
    Explicit human confirmation action triggering order placement.
    """
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    token = await session_store.get_swiggy_token(session_id)
    if not token:
        raise HTTPException(status_code=401, detail="Swiggy authentication required.")

    current_state = session["agent_state"]
    current_state["session_id"] = session_id
    current_state["swiggy_access_token"] = token
    current_state["user_confirmation"] = payload.user_confirmation
    current_state["payment_method"] = payload.payment_method
    current_state["needs_user_input"] = False

    clean_state = sanitize_state(current_state)
    await session_store.update_agent_state(
        session_id=session_id,
        agent_state=clean_state,
        current_step="PLACE_ORDER",
        needs_user_input=False
    )

    # Launch graph task in background
    asyncio.create_task(run_agent_background_task(session_id, current_state))

    return {
        "session_id": session_id,
        "status": "order_placement_started",
        "current_step": "PLACE_ORDER",
        "state": clean_state
    }
