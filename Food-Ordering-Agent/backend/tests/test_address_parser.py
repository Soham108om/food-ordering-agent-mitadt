import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mcp.parsers import parse_saved_addresses


def test_parse_saved_addresses_with_labels_and_details():
    response = [{
        "type": "text",
        "text": (
            "1. [Home] Soham: Second last House, Wagholi, Pune (ID: home_123)\n"
            "2. [Office] Soham: Business Bay, Pune (ID: office_456)"
        )
    }]

    assert parse_saved_addresses(response) == [
        {
            "id": "home_123",
            "label": "Home",
            "details": "Soham: Second last House, Wagholi, Pune"
        },
        {
            "id": "office_456",
            "label": "Office",
            "details": "Soham: Business Bay, Pune"
        }
    ]


def test_parse_saved_addresses_falls_back_to_generic_label():
    response = [{"type": "text", "text": "1. Pune address (ID: addr_123)"}]

    assert parse_saved_addresses(response) == [
        {
            "id": "addr_123",
            "label": "Saved address 1",
            "details": "Pune address"
        }
    ]


def test_parse_saved_addresses_deduplicates_ids():
    response = [{
        "type": "text",
        "text": "1. [Home] Pune (ID: addr_123)\n2. [Home] Pune (ID: addr_123)"
    }]

    assert len(parse_saved_addresses(response)) == 1
