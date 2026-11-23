import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.nodes import understand as understand_module
from app.agent.nodes.menu import menu_filter_node
from app.agent.nodes.understand import understand_node
from app.agent.state import AgentState


def test_vegetarian_preference_enforces_menu_filter(monkeypatch):
    monkeypatch.setattr(
        understand_module,
        "understand_with_gemini",
        lambda _request: {"food": "pizza", "vegetarian": False}
    )
    state = AgentState(
        user_request="I want pizza",
        vegetarian_preference=True,
        menu_options=[
            {"item_id": "veg_1", "name": "Vegetarian Pizza", "is_veg": True, "price": 200},
            {"item_id": "nonveg_1", "name": "Chicken Pizza", "is_veg": False, "price": 200}
        ]
    )

    understood = understand_node(state)
    filtered = menu_filter_node(understood)

    assert filtered["requirements"]["vegetarian"] is True
    assert [item["item_id"] for item in filtered["filtered_menu_items"]] == ["veg_1"]


def test_vegetarian_preference_does_not_override_when_disabled(monkeypatch):
    monkeypatch.setattr(
        understand_module,
        "understand_with_gemini",
        lambda _request: {"food": "pizza", "vegetarian": False}
    )
    state = AgentState(
        user_request="I want pizza",
        vegetarian_preference=False
    )

    result = understand_node(state)

    assert result["requirements"]["vegetarian"] is False
