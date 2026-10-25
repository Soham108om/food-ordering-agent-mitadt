from app.agent.state import AgentState
from app.mcp.client import invoke_mcp
from app.agent.nodes.utils import notify_state_update

async def cart_node(state: AgentState) -> AgentState:
    state["current_step"] = "CART"
    item = state.get("selected_item", {})
    restaurant = state.get("selected_restaurant", {})
    token = state.get("swiggy_access_token")

    print("🛒 CART")
    if not item or not token:
        print("❌ No item selected or missing token.")
        state["replanning_required"] = True
        notify_state_update(state)
        return state

    if item.get("has_variants"):
        print("⏸️ Variant selection required.")
        state["needs_user_input"] = True
        notify_state_update(state)
        return state

    try:
        cart_result = await invoke_mcp(
            "update_food_cart",
            {
                "restaurantId": state["selected_restaurant_id"],
                "addressId": state["selected_address_id"],
                "restaurantName": restaurant.get("name", ""),
                "cartItems": [
                    {
                        "menu_item_id": item["item_id"],
                        "quantity": 1
                    }
                ]
            },
            swiggy_access_token=token
        )
        state["cart_result"] = cart_result

        live_cart = await invoke_mcp(
            "get_food_cart",
            {
                "addressId": state["selected_address_id"],
                "restaurantName": restaurant.get("name", "")
            },
            swiggy_access_token=token
        )
        state["cart"] = live_cart
        print("✓ Cart updated and live cart retrieved")
        state["needs_user_input"] = False
    except Exception as e:
        print("❌ Cart operation failed:", type(e).__name__, str(e))
        state["error_message"] = str(e)
        state["replanning_required"] = True

    notify_state_update(state)
    return state
