import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.v1.agent import (
    ReorderContext,
    StartAgentRequest,
    _build_reorder_initial_values
)
from app.agent.nodes.menu import item_selection_node
from app.agent.routing import route_agent_entry
from app.agent.state import AgentState


def test_reorder_context_starts_from_menu_with_current_constraints():
    request = StartAgentRequest(
        user_request="Find my previous dish again",
        selected_address_id="current_address",
        vegetarian_preference=False,
        reorder_context=ReorderContext(
            restaurant_id="restaurant_1",
            restaurant_name="Previous Restaurant",
            item_id="old_dish_id",
            item_name="Favorite Pizza",
            is_veg=True,
            last_seen_price=250
        )
    )

    initial_state = AgentState(**_build_reorder_initial_values(
        request.reorder_context,
        request.vegetarian_preference
    ))

    assert route_agent_entry(initial_state) == "menu"
    assert initial_state["selected_restaurant_id"] == "restaurant_1"
    assert initial_state["requirements"]["food"] == "Favorite Pizza"
    assert initial_state["requirements"]["vegetarian"] is True


def test_normal_order_initialization_does_not_enter_reorder_path():
    initial_values = _build_reorder_initial_values(None, False)

    assert initial_values["resume_from"] is None
    assert initial_values["selected_restaurant_id"] is None
    assert initial_values["reorder_item_id"] is None


def test_reorder_selects_same_dish_by_name_if_provider_id_changed():
    state = AgentState(
        reorder_item_id="old_dish_id",
        reorder_item_name="Favorite Pizza",
        ranked_menu_items=[
            {"item_id": "other_id", "name": "Another Pizza", "price": 300},
            {"item_id": "current_dish_id", "name": "Favorite Pizza", "price": 275}
        ]
    )

    result = item_selection_node(state)

    assert result["selected_item"]["item_id"] == "current_dish_id"
    assert result["reorder_item_unavailable"] is False


def test_reorder_flags_missing_dish_and_preselects_available_alternative():
    state = AgentState(
        reorder_item_id="old_dish_id",
        reorder_item_name="Missing Pizza",
        ranked_menu_items=[
            {"item_id": "alternative_id", "name": "Available Pizza", "price": 300}
        ]
    )

    result = item_selection_node(state)

    assert result["reorder_item_unavailable"] is True
    assert result["selected_item"]["item_id"] == "alternative_id"
