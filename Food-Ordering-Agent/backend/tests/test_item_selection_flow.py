import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
import pytest

from app.api.v1.agent import _resolve_selected_menu_item, _resolve_selected_restaurant
from app.agent.nodes import cart as cart_module
from app.agent.nodes import menu as menu_module
from app.agent.nodes.menu import item_selection_node
from app.agent.nodes.restaurant import restaurant_selection_node
from app.agent.routing import (
    route_after_item_selection,
    route_after_restaurant_selection,
    route_agent_entry
)
from app.agent.state import AgentState


def test_item_selection_pauses_when_user_choice_is_enabled():
    state = AgentState(
        allow_item_selection=True,
        ranked_menu_items=[{"item_id": "dish_1", "name": "AI pick", "price": 200}]
    )

    result = item_selection_node(state)

    assert result["selected_item"]["item_id"] == "dish_1"
    assert result["current_step"] == "SELECT_ITEM"
    assert result["needs_user_input"] is True
    assert route_after_item_selection(result) == "waiting"


def test_item_selection_keeps_existing_auto_continue_by_default():
    state = AgentState(
        ranked_menu_items=[{"item_id": "dish_1", "name": "AI pick", "price": 200}]
    )

    result = item_selection_node(state)

    assert result["selected_item"]["item_id"] == "dish_1"
    assert result["needs_user_input"] is False
    assert route_after_item_selection(result) == "continue"


def test_resume_entry_defaults_to_existing_start_and_supports_order_stages():
    assert route_agent_entry(AgentState()) == "understand"
    assert route_agent_entry(AgentState(resume_from="customization")) == "customization"
    assert route_agent_entry(AgentState(resume_from="menu")) == "menu"
    assert route_agent_entry(AgentState(resume_from="payment")) == "payment"
    assert route_agent_entry(AgentState(resume_from="order")) == "order"

def test_restaurant_selection_pauses_with_ai_pick_preselected():
    state = AgentState(
        allow_restaurant_selection=True,
        ranked_restaurants=[
            {
                "restaurant_id": "rest_1",
                "name": "AI pick",
                "rating": 4.8,
                "delivery_minutes": 25
            }
        ]
    )

    result = restaurant_selection_node(state)

    assert result["selected_restaurant_id"] == "rest_1"
    assert result["needs_user_input"] is True
    assert route_after_restaurant_selection(result) == "waiting"

def test_restaurant_selection_preserves_existing_auto_continue_by_default():
    state = AgentState(
        ranked_restaurants=[{
            "restaurant_id": "rest_1",
            "name": "AI pick",
            "rating": 4.8,
            "delivery_minutes": 25
        }]
    )

    result = restaurant_selection_node(state)

    assert result["needs_user_input"] is False
    assert route_after_restaurant_selection(result) == "continue"


def test_selected_restaurant_must_be_current_and_ranked():
    state = {
        "current_step": "SELECT_RESTAURANT",
        "needs_user_input": True,
        "ranked_restaurants": [
            {"restaurant_id": "rest_1", "name": "AI pick"},
            {"restaurant_id": "rest_2", "name": "User choice"}
        ]
    }

    assert _resolve_selected_restaurant(state, "rest_2")["name"] == "User choice"
    with pytest.raises(HTTPException) as error:
        _resolve_selected_restaurant(state, "stale_restaurant")
    assert error.value.status_code == 400


def test_selected_restaurant_is_used_for_menu_search(monkeypatch):
    calls = []

    async def fake_invoke_mcp(tool_name, arguments, swiggy_access_token):
        calls.append((tool_name, arguments))
        return "1. Margherita Pizza — ₹200 | Veg (ID: dish_1)"

    monkeypatch.setattr(menu_module, "invoke_mcp", fake_invoke_mcp)
    state = AgentState(
        selected_restaurant_id="rest_2",
        selected_address_id="address_1",
        swiggy_access_token="test-token",
        requirements={"food": "pizza"}
    )

    asyncio.run(menu_module.menu_node(state))

    menu_search = next(args for name, args in calls if name == "search_menu")
    assert menu_search["restaurantIdOfAddedItem"] == "rest_2"


def test_selected_menu_item_must_be_current_and_ranked():
    state = {
        "current_step": "SELECT_ITEM",
        "needs_user_input": True,
        "ranked_menu_items": [
            {"item_id": "dish_1", "name": "AI pick"},
            {"item_id": "dish_2", "name": "User choice"}
        ]
    }

    assert _resolve_selected_menu_item(state, "dish_2")["name"] == "User choice"
    with pytest.raises(HTTPException) as error:
        _resolve_selected_menu_item(state, "stale_dish")
    assert error.value.status_code == 400


def test_cart_uses_the_confirmed_menu_item(monkeypatch):
    calls = []

    async def fake_invoke_mcp(tool_name, arguments, swiggy_access_token):
        calls.append((tool_name, arguments))
        if tool_name == "get_food_cart":
            return {
                "cartSummary": {
                    "itemSubtotal": 240,
                    "deliveryFee": 20,
                    "grandTotal": 260
                }
            }
        return {}

    monkeypatch.setattr(cart_module, "invoke_mcp", fake_invoke_mcp)
    state = AgentState(
        selected_item={"item_id": "dish_2", "name": "User choice", "price": 240},
        selected_restaurant_id="restaurant_1",
        selected_restaurant={"name": "Restaurant"},
        selected_address_id="address_1",
        swiggy_access_token="test-token"
    )

    asyncio.run(cart_module.cart_node(state))

    cart_update = next(args for name, args in calls if name == "update_food_cart")
    assert cart_update["cartItems"][0]["menu_item_id"] == "dish_2"
    assert state["cart_pricing"]["total_amount"] == 260
