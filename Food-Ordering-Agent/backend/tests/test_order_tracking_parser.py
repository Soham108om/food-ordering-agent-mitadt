import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mcp.parsers import parse_order_tracking


def test_parse_order_tracking_extracts_explicit_provider_fields():
    response = [{
        "type": "text",
        "text": (
            '{"orderStatus":"OUT_FOR_DELIVERY",'
            '"estimatedDeliveryMinutes":18,'
            '"statusMessage":"Your order is with the delivery partner."}'
        )
    }]

    assert parse_order_tracking(response) == {
        "status": "OUT_FOR_DELIVERY",
        "estimated_delivery": "18 min",
        "message": "Your order is with the delivery partner."
    }


def test_parse_order_tracking_reads_status_and_eta_from_formatted_text():
    response = [{
        "type": "text",
        "text": "Order status: Preparing\nEstimated delivery: 8:45 PM"
    }]

    assert parse_order_tracking(response) == {
        "status": "Preparing",
        "estimated_delivery": "8:45 PM",
        "message": None
    }


def test_parse_order_tracking_prefers_order_status_over_transport_status():
    response = {
        "status": "success",
        "data": {"orderStatus": "Preparing"}
    }

    assert parse_order_tracking(response)["status"] == "Preparing"


def test_parse_order_tracking_does_not_invent_status_for_unstructured_response():
    response = [{"type": "text", "text": "Tracking response is temporarily unavailable."}]

    assert parse_order_tracking(response) == {
        "status": None,
        "estimated_delivery": None,
        "message": None
    }
