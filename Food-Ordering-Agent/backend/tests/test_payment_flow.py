import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.nodes import payment as payment_module
from app.agent.nodes.payment import payment_node
from app.agent.state import AgentState


def test_payment_resume_reuses_options_instead_of_calling_swiggy_again(monkeypatch):
    calls = []

    async def fake_invoke_mcp(tool_name, arguments, swiggy_access_token):
        calls.append(tool_name)
        return {"available": True}

    monkeypatch.setattr(payment_module, "invoke_mcp", fake_invoke_mcp)
    state = AgentState(
        selected_address_id="address_1",
        swiggy_access_token="test-token",
        payment_options={"available": True},
        payment_method="Cash"
    )

    result = asyncio.run(payment_node(state))

    assert calls == []
    assert result["current_step"] == "PAYMENT"
    assert result["needs_user_input"] is False
    assert result["payment_method"] == "Cash"


def test_payment_node_fetches_options_when_not_already_available(monkeypatch):
    calls = []

    async def fake_invoke_mcp(tool_name, arguments, swiggy_access_token):
        calls.append((tool_name, arguments))
        return {"available": True}

    monkeypatch.setattr(payment_module, "invoke_mcp", fake_invoke_mcp)
    state = AgentState(
        selected_address_id="address_1",
        swiggy_access_token="test-token"
    )

    result = asyncio.run(payment_node(state))

    assert calls == [("get_payment_options", {"addressId": "address_1"})]
    assert result["payment_options"] == {"available": True}
    assert result["needs_user_input"] is True
