import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi import HTTPException

from app.api.v1 import agent as agent_api


@pytest.mark.asyncio
async def test_duplicate_start_during_start_reservation_returns_existing_session(monkeypatch):
    session_id = "session_starting"
    agent_api._PENDING_SESSION_OPERATIONS.add(session_id)

    async def existing_response(requested_session_id):
        return {
            "session_id": requested_session_id,
            "status": "already_running",
            "current_step": "START",
            "state": {}
        }

    monkeypatch.setattr(agent_api, "_already_running_response", existing_response)
    try:
        result = await agent_api.start_agent_workflow(
            agent_api.StartAgentRequest(user_request="pizza"),
            session_id
        )
    finally:
        agent_api._PENDING_SESSION_OPERATIONS.discard(session_id)

    assert result["status"] == "already_running"
    assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_duplicate_respond_while_operation_is_pending_returns_conflict():
    session_id = "session_responding"
    agent_api._PENDING_SESSION_OPERATIONS.add(session_id)
    try:
        with pytest.raises(HTTPException) as error:
            await agent_api.respond_to_agent(
                agent_api.RespondAgentRequest(payment_method="Cash"),
                session_id
            )
    finally:
        agent_api._PENDING_SESSION_OPERATIONS.discard(session_id)

    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_start_is_blocked_while_background_workflow_is_running(monkeypatch):
    session_id = "session_active"
    task = asyncio.create_task(asyncio.sleep(10))
    agent_api._ACTIVE_AGENT_TASKS[session_id] = task

    async def existing_response(requested_session_id):
        return {
            "session_id": requested_session_id,
            "status": "already_running",
            "current_step": "SEARCH_MENU",
            "state": {}
        }

    monkeypatch.setattr(agent_api, "_already_running_response", existing_response)
    try:
        result = await agent_api.start_agent_workflow(
            agent_api.StartAgentRequest(user_request="pizza"),
            session_id
        )
    finally:
        task.cancel()
        agent_api._ACTIVE_AGENT_TASKS.pop(session_id, None)

    assert result["status"] == "already_running"
    assert result["current_step"] == "SEARCH_MENU"
