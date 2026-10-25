from app.agent.state import AgentState
from app.agent.nodes.utils import notify_state_update

def replan_node(state: AgentState) -> AgentState:
    state["current_step"] = "REPLAN"
    print("🔄 REPLAN")
    print("The agent could not satisfy all hard constraints with the current result.")
    print("Asking user whether a constraint may be relaxed.")

    state["replanning_required"] = False
    state["needs_user_input"] = True
    notify_state_update(state)
    return state
