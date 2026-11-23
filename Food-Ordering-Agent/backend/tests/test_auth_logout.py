import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi import HTTPException, Response

from app.api.v1 import auth as auth_api
from app.db.session_store import SessionStore


@pytest.mark.asyncio
async def test_logout_deletes_server_session_and_expires_cookie(monkeypatch):
    deleted_sessions = []

    class FakeSessionStore:
        async def delete_session(self, session_id):
            deleted_sessions.append(session_id)

    monkeypatch.setattr(auth_api, "session_store", FakeSessionStore())
    monkeypatch.setattr(
        "app.api.v1.agent.is_agent_operation_active",
        lambda _session_id: False
    )
    response = Response()

    result = await auth_api.swiggy_logout(response, "session_1")

    assert result == {"status": "logged_out"}
    assert deleted_sessions == ["session_1"]
    set_cookie = response.headers["set-cookie"]
    assert "food_agent_session=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "HttpOnly" in set_cookie


@pytest.mark.asyncio
async def test_logout_is_rejected_while_agent_operation_is_active(monkeypatch):
    class FakeSessionStore:
        async def delete_session(self, _session_id):
            pytest.fail("An active session must not be deleted")

    monkeypatch.setattr(auth_api, "session_store", FakeSessionStore())
    monkeypatch.setattr(
        "app.api.v1.agent.is_agent_operation_active",
        lambda _session_id: True
    )

    with pytest.raises(HTTPException) as error:
        await auth_api.swiggy_logout(Response(), "session_1")

    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_session_store_deletes_only_the_requested_session(tmp_path):
    store = SessionStore(str(tmp_path / "sessions.db"))
    await store.init_db()
    await store.create_session("session_keep")
    await store.create_session("session_remove")

    await store.delete_session("session_remove")

    assert await store.get_session("session_remove") is None
    assert await store.get_session("session_keep") is not None
