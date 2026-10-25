import re
from app.agent.state import AgentState
from app.mcp.client import invoke_mcp
from app.mcp.parsers import extract_text
from app.agent.nodes.utils import notify_state_update

async def order_node(state: AgentState) -> AgentState:
    payment_method = state.get("payment_method")
    token = state.get("swiggy_access_token")

    if payment_method not in ("UPI", "Cash", "COD"):
        state["current_step"] = "PAYMENT"
        state["needs_user_input"] = True
        print("⏸️ Valid payment method required.")
        notify_state_update(state)
        return state

    # Separate Human Confirmation Safety Boundary
    if not state.get("user_confirmation", False):
        state["current_step"] = "CONFIRM_ORDER"
        state["needs_user_input"] = True
        print("⏸️ Waiting for explicit human confirmation. No real order placed.")
        notify_state_update(state)
        return state

    state["current_step"] = "PLACE_ORDER"
    print("📦 PLACE ORDER")

    try:
        arguments = {
            "addressId": state["selected_address_id"],
            "paymentMethod": payment_method
        }
        if payment_method == "UPI":
            intent_app = state.get("intent_app")
            generate_qr = state.get("generate_upi_qr")
            if intent_app:
                arguments["intentApp"] = intent_app
            elif generate_qr:
                arguments["generateUPIQR"] = True

        result = await invoke_mcp("place_food_order", arguments, swiggy_access_token=token)
    except Exception as e:
        print("❌ Order placement failed:", type(e).__name__, str(e))
        state["error_message"] = str(e)
        state["order_status"] = "FAILED"
        notify_state_update(state)
        return state

    state["order_result"] = result
    text = extract_text(result)

    order_patterns = [
        r'"orderId"\s*:\s*"([^"]+)"',
        r'"order_id"\s*:\s*"([^"]+)"',
        r"orderId\s*[:=]\s*([A-Za-z0-9_-]+)",
        r"Order ID\s*[:=]\s*([A-Za-z0-9_-]+)"
    ]

    for pattern in order_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            state["order_id"] = match.group(1)
            break

    upper_text = text.upper()
    if "PENDING_PAYMENT" in upper_text:
        state["order_status"] = "PENDING_PAYMENT"
        state["needs_user_input"] = True
        print("⏸️ UPI payment is pending.")
        notify_state_update(state)
        return state

    state["order_status"] = "PLACED"
    state["needs_user_input"] = False
    print("✓ Order placed successfully. Order ID:", state.get("order_id"))
    notify_state_update(state)
    return state

async def check_upi_payment_status(state: AgentState) -> AgentState:
    order_id = state.get("order_id")
    token = state.get("swiggy_access_token")

    if not order_id or not token:
        print("❌ No order ID or token available.")
        return state

    order_result = state.get("order_result")
    text = extract_text(order_result)

    def extract_value(key):
        match = re.search(rf'"{re.escape(key)}"\s*:\s*"([^"]+)"', text, re.IGNORECASE)
        return match.group(1) if match else None

    paas_id = extract_value("paasId")
    address_id = state.get("selected_address_id")

    arguments = {"orderId": order_id, "addressId": address_id}
    if paas_id:
        arguments["paasId"] = paas_id

    try:
        result = await invoke_mcp("check_payment_status", arguments, swiggy_access_token=token)
        state["payment_status_result"] = result
        print("✓ Payment status retrieved")
    except Exception as e:
        print("❌ Payment status check failed:", type(e).__name__, str(e))

    notify_state_update(state)
    return state
