from app.agent.state import AgentState
from app.mcp.client import invoke_mcp
from app.agent.nodes.utils import notify_state_update

async def tracking_node(state: AgentState) -> AgentState:
    state["current_step"] = "TRACK"
    order_id = state.get("order_id")
    token = state.get("swiggy_access_token")

    if not order_id or not token:
        print("ℹ️ No order ID or token available for tracking.")
        notify_state_update(state)
        return state

    print("🚴 TRACK ORDER")
    try:
        result = await invoke_mcp("track_food_order", {"orderId": order_id}, swiggy_access_token=token)
        state["tracking_result"] = result
        print("✓ Live tracking retrieved")
    except Exception as e:
        print("❌ Tracking failed:", type(e).__name__, str(e))
        state["error_message"] = str(e)

    notify_state_update(state)
    return state
