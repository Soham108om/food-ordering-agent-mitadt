import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app.api.v1 import stream as stream_api


@pytest.mark.asyncio
async def test_stream_stays_open_across_user_pause_and_emits_resumed_dish_state(monkeypatch):
    states = [
        {
            "current_step": "SELECT_RESTAURANT",
            "needs_user_input": True,
            "replanning_required": False,
            "agent_state": {"current_step": "SELECT_RESTAURANT", "needs_user_input": True}
        },
        {
            "current_step": "SELECT_RESTAURANT",
            "needs_user_input": True,
            "replanning_required": False,
            "agent_state": {"current_step": "SELECT_RESTAURANT", "needs_user_input": True}
        },
        {
            "current_step": "SELECT_RESTAURANT",
            "needs_user_input": False,
            "replanning_required": False,
            "agent_state": {"current_step": "SELECT_RESTAURANT", "needs_user_input": False}
        },
        {
            "current_step": "SELECT_ITEM",
            "needs_user_input": True,
            "replanning_required": False,
            "agent_state": {
                "current_step": "SELECT_ITEM",
                "needs_user_input": True,
                "selected_item": {"item_id": "dish_1", "name": "Margherita Pizza"}
            }
        },
        {
            "current_step": "TRACK",
            "needs_user_input": False,
            "replanning_required": False,
            "agent_state": {"current_step": "TRACK"}
        }
    ]
    calls = 0

    async def get_session(_session_id):
        nonlocal calls
        state = states[min(calls, len(states) - 1)]
        calls += 1
        return state

    async def no_wait(_seconds):
        return None

    monkeypatch.setattr(stream_api.session_store, "get_session", get_session)
    monkeypatch.setattr(stream_api.asyncio, "sleep", no_wait)

    response = await stream_api.stream_agent_events("session_1")
    events = []
    async for chunk in response.body_iterator:
        if isinstance(chunk, dict):
            events.append(chunk)

    updates = [
        json.loads(event["data"])
        for event in events
        if event["event"] == "agent_update"
    ]
    idle_events = [
        json.loads(event["data"])
        for event in events
        if event["event"] == "agent_idle"
    ]

    dish_update = next(update for update in updates if update["current_step"] == "SELECT_ITEM")
    assert dish_update["state"]["selected_item"]["name"] == "Margherita Pizza"
    assert idle_events == [{"status": "paused_or_completed", "step": "TRACK"}]
    assert calls >= 5
