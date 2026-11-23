from app.agent.state import AgentState
from app.mcp.client import invoke_mcp
from app.agent.nodes.utils import notify_state_update

async def payment_node(state: AgentState) -> AgentState:
    state["current_step"] = "PAYMENT"
    token = state.get("swiggy_access_token")
    print("💳 PAYMENT")

    if not token:
        print("❌ Missing token.")
        state["error_message"] = "Swiggy authentication token missing."
        state["needs_user_input"] = True
        notify_state_update(state)
        return state

    if state.get("payment_options") is None:
        try:
            result = await invoke_mcp(
                "get_payment_options",
                {
                    "addressId": state["selected_address_id"]
                },
                swiggy_access_token=token
            )
            state["payment_options"] = result
            state.pop("error_message", None)
            print("✓ Live payment options retrieved")
        except Exception as e:
            print("❌ Payment options failed:", type(e).__name__, str(e))
            state["error_message"] = str(e)
            state["needs_user_input"] = True
            notify_state_update(state)
            return state
    else:
        print("✓ Reusing previously retrieved payment options")

    payment_method = state.get("payment_method")
    if not payment_method:
        state["needs_user_input"] = True
        print("⏸️ Waiting for user payment selection.")
        notify_state_update(state)
        return state

    state["needs_user_input"] = False
    print("✓ Payment method:", payment_method)
    notify_state_update(state)
    return state
