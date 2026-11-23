import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mcp.parsers import parse_cart_pricing


def test_parse_cart_pricing_extracts_provider_total_and_explicit_charges():
    response = [{
        "type": "text",
        "text": (
            '{"cartSummary":{"itemSubtotal":"₹200","deliveryFee":"₹25",'
            '"tax":12,"grandTotal":"₹237"}}'
        )
    }]

    assert parse_cart_pricing(response) == {
        "total_amount": 237.0,
        "item_subtotal": 200.0,
        "charges": [
            {"label": "Delivery fee", "amount": 25.0},
            {"label": "Tax", "amount": 12.0}
        ]
    }


def test_parse_cart_pricing_reads_explicit_total_from_formatted_text():
    response = [{"type": "text", "text": "Cart total: ₹237"}]

    assert parse_cart_pricing(response) == {
        "total_amount": 237.0,
        "item_subtotal": None,
        "charges": []
    }


def test_parse_cart_pricing_does_not_infer_total_from_item_or_fee_prices():
    response = [{"type": "text", "text": "Item ₹200; delivery fee ₹25"}]

    assert parse_cart_pricing(response) == {
        "total_amount": None,
        "item_subtotal": None,
        "charges": []
    }
