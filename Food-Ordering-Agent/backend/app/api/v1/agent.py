import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.api.deps import get_session_id
from app.db.session_store import session_store, safe_json_dumps
from app.mcp.client import invoke_mcp, format_mcp_error
from app.mcp.parsers import extract_first_id, extract_text, parse_saved_addresses
from app.agent.graph import food_agent
from app.agent.state import AgentState
from app.agent.nodes.utils import sanitize_state, set_event_loop

router = APIRouter(prefix="/agent", tags=["Agent"])

class ReorderContext(BaseModel):
    restaurant_id: str
    restaurant_name: str
    item_id: str
    item_name: str
    is_veg: bool = False
    last_seen_price: Optional[float] = None

class StartAgentRequest(BaseModel):
    user_request: str
    selected_address_id: Optional[str] = None
    allow_restaurant_selection: bool = False
    allow_item_selection: bool = False
    vegetarian_preference: bool = False
    reorder_context: Optional[ReorderContext] = None
    # UNIT-3: stable user identity for long-term memory lookup
    user_id: Optional[str] = None

class RespondAgentRequest(BaseModel):
    payment_method: Optional[str] = None
    relaxed_constraints: Optional[Dict[str, Any]] = None
    selected_restaurant_id: Optional[str] = None
    selected_menu_item_id: Optional[str] = None

class ConfirmOrderRequest(BaseModel):
    user_confirmation: bool = True
    payment_method: str = "COD"

# Terminal/Waiting steps where an agent execution graph is NOT actively running in background
IDLE_OR_WAITING_STEPS = {
    "INIT", "START", "END", "TRACK", "ERROR", "PAYMENT", "CONFIRM_ORDER", "REPLAN", None
}

_PENDING_SESSION_OPERATIONS = set()
_ACTIVE_AGENT_TASKS: Dict[str, asyncio.Task] = {}

def _agent_task_is_running(session_id: str) -> bool:
    task = _ACTIVE_AGENT_TASKS.get(session_id)
    return task is not None and not task.done()

def is_agent_operation_active(session_id: str) -> bool:
    return session_id in _PENDING_SESSION_OPERATIONS or _agent_task_is_running(session_id)

def _clear_agent_task(session_id: str, task: asyncio.Task) -> None:
    if _ACTIVE_AGENT_TASKS.get(session_id) is task:
        _ACTIVE_AGENT_TASKS.pop(session_id, None)

async def _already_running_response(session_id: str) -> Dict[str, Any]:
    existing_session = await session_store.get_session(session_id)
    return {
        "session_id": session_id,
        "status": "already_running",
        "current_step": existing_session.get("current_step") if existing_session else None,
        "state": existing_session.get("agent_state") if existing_session else None
    }


def _derive_user_from_session(session_id: str) -> str:
    """
    Derive a stable long-term user identity from the session id.

    The session id is a per-conversation identifier, so we cannot use it
    directly: long-term memory must survive across sessions. We therefore
    derive a stable per-browser identity from the session id's stable
    component. In a production deployment this would be the authenticated
    account id; for the demo it is derived deterministically.
    """
    import hashlib

    stable = session_id.split(":")[0] if ":" in session_id else session_id
    digest = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]
    return f"user_{digest}"

def _resolve_selected_menu_item(state: Dict[str, Any], item_id: str) -> Dict[str, Any]:
    if state.get("current_step") != "SELECT_ITEM" or not state.get("needs_user_input"):
        raise HTTPException(status_code=409, detail="Dish selection is not currently awaiting confirmation.")

    for item in state.get("ranked_menu_items", []):
        if str(item.get("item_id", "")) == item_id:
            return item

    raise HTTPException(status_code=400, detail="Selected dish is not in the current menu results.")

def _resolve_selected_restaurant(state: Dict[str, Any], restaurant_id: str) -> Dict[str, Any]:
    if state.get("current_step") != "SELECT_RESTAURANT" or not state.get("needs_user_input"):
        raise HTTPException(status_code=409, detail="Restaurant selection is not currently awaiting confirmation.")

    for restaurant in state.get("ranked_restaurants", []):
        if str(restaurant.get("restaurant_id", "")) == restaurant_id:
            return restaurant

    raise HTTPException(status_code=400, detail="Selected restaurant is not in the current results.")

def _build_reorder_initial_values(
    reorder: Optional[ReorderContext],
    vegetarian_preference: bool
) -> Dict[str, Any]:
    if not reorder:
        return {
            "resume_from": None,
            "selected_restaurant": {},
            "selected_restaurant_id": None,
            "reorder_item_id": None,
            "reorder_item_name": None,
            "reorder_item_unavailable": False,
            "requirements": {}
        }

    if not all((
        reorder.restaurant_id.strip(),
        reorder.restaurant_name.strip(),
        reorder.item_id.strip(),
        reorder.item_name.strip()
    )):
        raise HTTPException(status_code=400, detail="Reorder details are incomplete.")

    restaurant_id = reorder.restaurant_id.strip()
    restaurant_name = reorder.restaurant_name.strip()
    item_id = reorder.item_id.strip()
    item_name = reorder.item_name.strip()

    return {
        "resume_from": "menu",
        "selected_restaurant": {
            "restaurant_id": restaurant_id,
            "name": restaurant_name
        },
        "selected_restaurant_id": restaurant_id,
        "reorder_item_id": item_id,
        "reorder_item_name": item_name,
        "reorder_item_unavailable": False,
        "requirements": {
            "food": item_name,
            "vegetarian": vegetarian_preference or reorder.is_veg
        }
    }

def _apply_relaxed_constraints(
    state: Dict[str, Any],
    relaxed_constraints: Dict[str, Any]
) -> None:
    constraints = dict(relaxed_constraints)
    requirements = state.get("requirements", {})
    no_match_details = state.get("no_match_details") or {}

    if "food" in constraints:
        food = str(constraints["food"]).strip()
        if not food:
            raise HTTPException(status_code=400, detail="A broader food or cuisine search term is required.")
        constraints["food"] = food
        requirements.pop("food_components", None)
        requirements.pop("cuisine", None)
        state["food_components"] = []
        state["cuisine"] = None
        state.pop("reorder_item_id", None)
        state.pop("reorder_item_name", None)
        state["reorder_item_unavailable"] = False

    if "vegetarian" in constraints and not isinstance(constraints["vegetarian"], bool):
        raise HTTPException(status_code=400, detail="Vegetarian preference must be true or false.")

    requirements.update(constraints)
    state["requirements"] = requirements
    state["replanning_required"] = False
    state["no_match_details"] = None
    state.pop("error_message", None)
    state["resume_from"] = (
        "menu"
        if no_match_details.get("stage") == "menu" and "food" not in constraints
        else "restaurant_search"
    )

async def run_agent_background_task(session_id: str, state: AgentState):
    """Executes the LangGraph workflow asynchronously in the background."""
    # Sync nodes run in a worker thread, so they need a handle on this loop to
    # persist their live state updates.
    set_event_loop(asyncio.get_running_loop())
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

def _launch_agent_task(session_id: str, state: AgentState) -> None:
    task = asyncio.create_task(run_agent_background_task(session_id, state))
    _ACTIVE_AGENT_TASKS[session_id] = task
    task.add_done_callback(lambda finished: _clear_agent_task(session_id, finished))

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
        addresses = parse_saved_addresses(raw_addresses)

        return {
            "status": "ok",
            "raw_response": json.loads(safe_json_dumps(raw_addresses)),
            "formatted_text": text_addresses,
            "first_address_id": first_address_id,
            "addresses": addresses
        }
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to retrieve Swiggy addresses: {format_mcp_error(e)}"
        ) from e

@router.post("/start")
async def start_agent_workflow(
    payload: StartAgentRequest,
    session_id: str = Depends(get_session_id)
):
    if session_id in _PENDING_SESSION_OPERATIONS or _agent_task_is_running(session_id):
        return await _already_running_response(session_id)

    _PENDING_SESSION_OPERATIONS.add(session_id)
    try:
        return await _start_agent_workflow_impl(payload, session_id)
    finally:
        _PENDING_SESSION_OPERATIONS.discard(session_id)

async def _start_agent_workflow_impl(
    payload: StartAgentRequest,
    session_id: str
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
        addr_res = await get_swiggy_addresses(session_id)
        address_id = addr_res.get("first_address_id")

    if not address_id:
        raise HTTPException(status_code=400, detail="No delivery address available in your Swiggy account.")

    # Fresh state initialization for NEW request while preserving OAuth token and Address
    # UNIT-3 FEEDBACK LOOP: attach the user's long-term identity so the
    # ranking node can pick up learned weights on every subsequent request.
    user_id = payload.user_id or _derive_user_from_session(session_id)
    reorder = payload.reorder_context
    reorder_initial_values = _build_reorder_initial_values(
        reorder,
        payload.vegetarian_preference
    )

    initial_state = AgentState(
        session_id=session_id,
        user_id=user_id,
        swiggy_access_token=token,
        user_request=payload.user_request,
        selected_address_id=address_id,
        allow_restaurant_selection=payload.allow_restaurant_selection,
        allow_item_selection=payload.allow_item_selection,
        vegetarian_preference=payload.vegetarian_preference,
        **reorder_initial_values,
        cuisine=None,
        food_components=[],
        restaurants=[],
        parsed_restaurants=[],
        filtered_restaurants=[],
        ranked_restaurants=[],
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
        tracking_summary=None,
        tracking_error=None,
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
    _launch_agent_task(session_id, initial_state)

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
    if session_id in _PENDING_SESSION_OPERATIONS or _agent_task_is_running(session_id):
        raise HTTPException(status_code=409, detail="The workflow is still processing the previous action.")

    _PENDING_SESSION_OPERATIONS.add(session_id)
    try:
        return await _respond_to_agent_impl(payload, session_id)
    finally:
        _PENDING_SESSION_OPERATIONS.discard(session_id)

async def _respond_to_agent_impl(
    payload: RespondAgentRequest,
    session_id: str
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
    current_step = current_state.get("current_step")

    if payload.selected_restaurant_id and payload.selected_menu_item_id:
        raise HTTPException(status_code=400, detail="Select either a restaurant or a dish at a time.")

    if payload.selected_restaurant_id:
        selected_restaurant = _resolve_selected_restaurant(
            current_state,
            payload.selected_restaurant_id
        )
        current_state["selected_restaurant"] = selected_restaurant
        current_state["selected_restaurant_id"] = selected_restaurant["restaurant_id"]
        current_state["resume_from"] = "menu"
    elif current_step == "SELECT_RESTAURANT" and current_state.get("needs_user_input"):
        raise HTTPException(status_code=400, detail="Choose a restaurant before continuing.")

    if payload.selected_menu_item_id:
        current_state["selected_item"] = _resolve_selected_menu_item(
            current_state,
            payload.selected_menu_item_id
        )
        current_state["resume_from"] = "customization"
    elif current_step == "SELECT_ITEM" and current_state.get("needs_user_input"):
        raise HTTPException(status_code=400, detail="Choose a dish before continuing.")

    current_state["session_id"] = session_id
    current_state["swiggy_access_token"] = token
    current_state["needs_user_input"] = False

    if payload.payment_method:
        current_state["payment_method"] = payload.payment_method
        if current_step == "PAYMENT":
            current_state["resume_from"] = "payment"

    if payload.relaxed_constraints:
        _apply_relaxed_constraints(current_state, payload.relaxed_constraints)

    clean_state = sanitize_state(current_state)
    await session_store.update_agent_state(
        session_id=session_id,
        agent_state=clean_state,
        current_step=clean_state.get("current_step", "RESUMING"),
        needs_user_input=False
    )

    # Launch graph task in background
    _launch_agent_task(session_id, current_state)

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
    if session_id in _PENDING_SESSION_OPERATIONS or _agent_task_is_running(session_id):
        raise HTTPException(status_code=409, detail="The workflow is still processing the previous action.")

    _PENDING_SESSION_OPERATIONS.add(session_id)
    try:
        return await _confirm_and_place_order_impl(payload, session_id)
    finally:
        _PENDING_SESSION_OPERATIONS.discard(session_id)

async def _confirm_and_place_order_impl(
    payload: ConfirmOrderRequest,
    session_id: str
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
    current_state["resume_from"] = "order"

    clean_state = sanitize_state(current_state)
    await session_store.update_agent_state(
        session_id=session_id,
        agent_state=clean_state,
        current_step="PLACE_ORDER",
        needs_user_input=False
    )

    # Launch graph task in background
    _launch_agent_task(session_id, current_state)

    return {
        "session_id": session_id,
        "status": "order_placement_started",
        "current_step": "PLACE_ORDER",
        "state": clean_state
    }
