import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mcp.parsers import parse_menu_response


def test_menu_parser_extracts_rating_count_and_serving_label():
    response = [{
        "type": "text",
        "text": (
            '1. OG Margherita Pizza [7" Regular] — ₹198 | Veg | '
            '4.9★ (17) (ID: 179098835)'
        )
    }]

    item = parse_menu_response(response)[0]

    assert item["name"] == "OG Margherita Pizza"
    assert item["serving_label"] == '7" Regular'
    assert item["rating"] == 4.9
    assert item["rating_count"] == 17


def test_menu_parser_keeps_details_optional_when_source_omits_them():
    response = [{"type": "text", "text": "1. Plain Pizza — ₹200 | Veg (ID: dish_1)"}]

    item = parse_menu_response(response)[0]

    assert item["rating"] is None
    assert item["rating_count"] is None
    assert item["serving_label"] is None
