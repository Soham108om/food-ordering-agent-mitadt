from app.agent.state import AgentState
from app.mcp.client import invoke_mcp
from app.agent.nodes.utils import notify_state_update

async def customization_node(state: AgentState) -> AgentState:
    state["current_step"] = "CUSTOMIZATION"
    item = state.get("selected_item", {})
    token = state.get("swiggy_access_token")

    print("⚙️ CUSTOMIZATION")
    if not item or not token:
        print("❌ No selected item or missing token.")
        state["replanning_required"] = True
        notify_state_update(state)
        return state

    try:
        result = await invoke_mcp(
            "search_menu",
            {
                "addressId": state["selected_address_id"],
                "query": item["name"],
                "restaurantIdOfAddedItem": str(state["selected_restaurant_id"]),
                "vegFilter": 1,
                "offset": 0
            },
            swiggy_access_token=token
        )
        state["customization_result"] = result
        state["selected_customization"] = {}
        print("✓ Exact item customization data retrieved")
    except Exception as e:
        print("⚠️ Customization lookup failed:", str(e))
        state["customization_result"] = None
        state["selected_customization"] = {}

    if item.get("has_variants") or item.get("has_addons"):
        print("ℹ️ Item supports variants/add-ons.")
    else:
        print("ℹ️ No customization required.")

    notify_state_update(state)
    return state
