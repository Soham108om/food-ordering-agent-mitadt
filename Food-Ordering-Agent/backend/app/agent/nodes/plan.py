from app.agent.state import AgentState
from app.agent.nodes.utils import notify_state_update

def plan_node(state: AgentState) -> AgentState:
    state["current_step"] = "PLAN"
    print("🗺️ CREATE TASK PLAN")
    steps = [
        "Get address",
        "Search restaurants",
        "Filter hard constraints",
        "Rank restaurants",
        "Select restaurant",
        "Search menu",
        "Filter menu items",
        "Rank menu items",
        "Select item",
        "Check customization",
        "Update cart",
        "Get payment options",
        "Ask confirmation",
        "Place order",
        "Track order",
    ]
    for i, step in enumerate(steps, 1):
        print(f"{i}. {step}")
    notify_state_update(state)
    return state
