from app.agent.state import AgentState
from app.mcp.client import invoke_mcp
from app.mcp.parsers import parse_order_tracking
from app.agent.nodes.utils import notify_state_update

async def tracking_node(state: AgentState) -> AgentState:
    state["current_step"] = "TRACK"
    order_id = state.get("order_id")
    token = state.get("swiggy_access_token")
    state["tracking_result"] = None
    state["tracking_summary"] = None
    state["tracking_error"] = None

    if not order_id:
        state["tracking_error"] = "Swiggy did not return an order ID, so tracking is unavailable."
        print("ℹ️ No order ID available for tracking.")
        notify_state_update(state)
        return state
    if not token:
        state["tracking_error"] = "Swiggy authentication is unavailable, so tracking could not be retrieved."
        print("ℹ️ No access token available for tracking.")
        notify_state_update(state)
        return state

    print("🚴 TRACK ORDER")
    try:
        result = await invoke_mcp("track_food_order", {"orderId": order_id}, swiggy_access_token=token)
        state["tracking_result"] = result
        state["tracking_summary"] = parse_order_tracking(result)
        if not any(state["tracking_summary"].values()):
            state["tracking_error"] = "Swiggy returned no readable tracking details."
            print("ℹ️ Swiggy returned no readable tracking details.")
        else:
            print("✓ Tracking update retrieved")
    except Exception as e:
        print("❌ Tracking failed:", type(e).__name__, str(e))
        state["error_message"] = str(e)
        state["tracking_error"] = "Could not retrieve the latest tracking update from Swiggy."

    notify_state_update(state)
    return state
