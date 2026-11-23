import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mcp.parsers import parse_menu_response, parse_restaurant_response


def test_restaurant_parser_keeps_a_provider_image_url_when_available():
    response = {
        "restaurants": [{
            "id": "restaurant_1",
            "name": "Pizza House",
            "cuisines": ["Pizza"],
            "avgRating": 4.5,
            "deliveryTimeMinutes": 25,
            "availabilityStatus": "OPEN",
            "imageUrl": "https://media-assets.swiggy.com/restaurant.jpg"
        }]
    }

    restaurant = parse_restaurant_response(response)[0]

    assert restaurant["image_url"] == "https://media-assets.swiggy.com/restaurant.jpg"


def test_parsers_reject_non_https_or_non_swiggy_image_urls():
    restaurant_response = {
        "restaurants": [{
            "id": "restaurant_1",
            "name": "Pizza House",
            "cuisines": ["Pizza"],
            "avgRating": 4.5,
            "deliveryTimeMinutes": 25,
            "availabilityStatus": "OPEN",
            "imageUrl": "http://example.com/restaurant.jpg"
        }]
    }
    menu_response = [{
        "type": "text",
        "text": (
            "1. Plain Pizza — ₹200 | Veg (ID: dish_1) "
            "(Image URL: https://example.com/dish.jpg)"
        )
    }]

    assert parse_restaurant_response(restaurant_response)[0]["image_url"] is None
    assert parse_menu_response(menu_response)[0]["image_url"] is None


def test_menu_parser_extracts_a_trusted_image_url_when_provider_includes_it():
    response = [{
        "type": "text",
        "text": (
            "1. Plain Pizza — ₹200 | Veg (ID: dish_1) "
            "(Image URL: https://media-assets.swiggy.com/dish.jpg)"
        )
    }]

    item = parse_menu_response(response)[0]

    assert item["name"] == "Plain Pizza"
    assert item["image_url"] == "https://media-assets.swiggy.com/dish.jpg"


def test_image_url_remains_optional_when_provider_omits_it():
    restaurant = parse_restaurant_response({
        "restaurants": [{
            "id": "restaurant_1",
            "name": "Pizza House",
            "cuisines": ["Pizza"],
            "avgRating": 4.5,
            "deliveryTimeMinutes": 25,
            "availabilityStatus": "OPEN"
        }]
    })[0]
    item = parse_menu_response([
        {"type": "text", "text": "1. Plain Pizza — ₹200 | Veg (ID: dish_1)"}
    ])[0]

    assert restaurant["image_url"] is None
    assert item["image_url"] is None
