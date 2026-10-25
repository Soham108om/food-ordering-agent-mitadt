from app.agent.state import AgentState

def route_after_restaurant_rank(state: AgentState) -> str:
    if state.get("replanning_required"):
        return "replan"
    return "continue"

def route_after_menu_rank(state: AgentState) -> str:
    if state.get("replanning_required"):
        return "replan"
    return "continue"

def route_after_cart(state: AgentState) -> str:
    if state.get("needs_user_input"):
        return "waiting"
    if state.get("replanning_required"):
        return "replan"
    return "payment"

def route_after_payment(state: AgentState) -> str:
    if state.get("needs_user_input"):
        return "waiting"
    return "order"

def route_after_order(state: AgentState) -> str:
    if not state.get("user_confirmation"):
        return "end"  # Human confirmation checkpoint pause
    if state.get("order_status") in ("FAILED", "PENDING_PAYMENT"):
        return "end"
    if state.get("order_id"):
        return "tracking"
    return "end"
