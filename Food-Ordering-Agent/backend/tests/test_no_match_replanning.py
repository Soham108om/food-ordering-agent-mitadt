import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.nodes.menu import menu_filter_node
from app.agent.nodes.replan import replan_node
from app.agent.nodes.restaurant import restaurant_filter_node
from app.agent.routing import route_agent_entry
from app.agent.state import AgentState
from app.api.v1.agent import _apply_relaxed_constraints


def test_restaurant_no_match_reports_actual_rejection_reasons():
    state = AgentState(
        restaurants={
            "restaurants": [
                {
                    "id": "slow",
                    "name": "Pizza House",
                    "cuisines": ["Pizza"],
                    "avgRating": 4.2,
                    "deliveryTimeMinutes": 50,
                    "availabilityStatus": "OPEN"
                },
                {
                    "id": "closed",
                    "name": "Pizza Closed",
                    "cuisines": ["Pizza"],
                    "avgRating": 4.0,
                    "deliveryTimeMinutes": 20,
                    "availabilityStatus": "CLOSED"
                },
                {
                    "id": "mismatch",
                    "name": "Sushi House",
                    "cuisines": ["Japanese"],
                    "avgRating": 4.1,
                    "deliveryTimeMinutes": 20,
                    "availabilityStatus": "OPEN"
                }
            ]
        },
        requirements={"food": "pizza", "max_delivery_minutes": 30}
    )

    result = restaurant_filter_node(state)

    assert result["filtered_restaurants"] == []
    assert result["no_match_details"] == {
        "stage": "restaurants",
        "candidate_count": 3,
        "reasons": {
            "delivery_time": 1,
            "delivery_time_unavailable": 0,
            "closed": 1,
            "food_mismatch": 1
        },
        "suggestions": ["delivery_time", "food"]
    }


def test_menu_no_match_suggests_only_adjustments_relevant_to_rejections():
    state = AgentState(
        menu_options=[
            {"item_id": "expensive", "name": "Pizza Special", "price": 700, "is_veg": True},
            {"item_id": "nonveg", "name": "Chicken Pizza", "price": 450, "is_veg": False},
            {"item_id": "mismatch", "name": "Veg Burger", "price": 300, "is_veg": True}
        ],
        requirements={"food": "pizza", "vegetarian": True, "max_budget": 500}
    )

    result = menu_filter_node(state)

    assert result["filtered_menu_items"] == []
    assert result["no_match_details"]["stage"] == "menu"
    assert result["no_match_details"]["candidate_count"] == 3
    assert result["no_match_details"]["reasons"] == {
        "food_mismatch": 1,
        "vegetarian": 1,
        "budget": 1
    }
    assert result["no_match_details"]["suggestions"] == [
        "budget", "vegetarian", "food"
    ]


def test_replanning_preserves_explanation_and_waits_for_user_choice():
    details = {
        "stage": "menu",
        "candidate_count": 2,
        "reasons": {"budget": 2},
        "suggestions": ["budget"]
    }
    state = AgentState(no_match_details=details, replanning_required=True)

    result = replan_node(state)

    assert result["current_step"] == "REPLAN"
    assert result["needs_user_input"] is True
    assert result["no_match_details"] == details


def test_relaxed_search_constraints_resume_without_overwriting_user_edits():
    state = {
        "requirements": {
            "food": "vegetarian pizza",
            "food_components": ["pizza"],
            "cuisine": "Italian",
            "vegetarian": True
        },
        "food_components": ["pizza"],
        "cuisine": "Italian",
        "reorder_item_id": "old-item",
        "reorder_item_name": "Old Pizza",
        "reorder_item_unavailable": True,
        "no_match_details": {"stage": "menu"}
    }

    _apply_relaxed_constraints(state, {
        "food": "Italian food",
        "max_budget": 700
    })

    assert route_agent_entry(state) == "restaurant_search"
    assert state["requirements"]["food"] == "Italian food"
    assert state["requirements"]["max_budget"] == 700
    assert "food_components" not in state["requirements"]
    assert "cuisine" not in state["requirements"]
    assert state["food_components"] == []
    assert "reorder_item_id" not in state
    assert "reorder_item_name" not in state
    assert state["no_match_details"] is None


def test_replanning_rejects_an_empty_food_search():
    with pytest.raises(HTTPException) as error:
        _apply_relaxed_constraints({"requirements": {}}, {"food": "  "})

    assert error.value.status_code == 400


def test_menu_constraint_adjustment_keeps_the_selected_restaurant():
    state = {
        "requirements": {"food": "pizza", "max_budget": 300},
        "selected_restaurant_id": "restaurant-1",
        "no_match_details": {"stage": "menu"}
    }

    _apply_relaxed_constraints(state, {"max_budget": 500})

    assert route_agent_entry(state) == "menu"
    assert state["selected_restaurant_id"] == "restaurant-1"
