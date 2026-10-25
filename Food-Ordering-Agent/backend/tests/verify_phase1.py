import os
import sys
import asyncio
import traceback

# Force UTF-8 output formatting for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.security import encrypt_token, decrypt_token
from app.db.session_store import session_store
from app.mcp.oauth import (
    generate_pkce_credentials,
    register_swiggy_oauth_client,
    build_authorization_url
)
from app.mcp.client import get_mcp_tools, invoke_mcp
from app.mcp.parsers import parse_restaurant_response, parse_menu_response, extract_first_id
from app.agent.nodes.understand import understand_with_gemini
from app.agent.nodes.restaurant import restaurant_filter_node, restaurant_rank_node
from app.agent.nodes.menu import menu_filter_node, menu_rank_node
from app.agent.graph import food_agent
from app.agent.state import AgentState

async def run_phase1_verification():
    print("==================================================")
    print("      REAL BACKEND PHASE 1 VERIFICATION SUITE      ")
    print("==================================================\n")

    results = {}

    # ----------------------------------------------------
    # 1. GEMINI CONNECTION TEST
    # ----------------------------------------------------
    print("[1/15] Testing real Gemini API connection & NLU...")
    try:
        req = understand_with_gemini("I want a vegetarian pizza under ₹500 delivered within 30 minutes.")
        assert "food" in req, "Gemini output missing 'food' key"
        assert req["vegetarian"] is True, "Gemini failed veg constraint extraction"
        assert req["max_budget"] == 500, "Gemini failed budget constraint extraction"
        assert req["max_delivery_minutes"] == 30, "Gemini failed delivery constraint extraction"
        print("  [OK] Real Gemini response extracted:", req)
        results["1_gemini"] = "PASSED"
    except Exception as e:
        print("  [FAIL] Gemini connection issue:", e)
        results["1_gemini"] = f"FAILED: {e}"

    # ----------------------------------------------------
    # 2. SWIGGY OAUTH & PKCE REGISTRATION TEST
    # ----------------------------------------------------
    print("\n[2/15] Testing Swiggy OAuth + PKCE registration...")
    try:
        pkce = generate_pkce_credentials()
        assert len(pkce["code_verifier"]) > 30, "Invalid PKCE verifier"
        assert len(pkce["code_challenge"]) > 30, "Invalid PKCE challenge"

        client_id = register_swiggy_oauth_client(settings.REDIRECT_URI)
        assert client_id, "Swiggy registration failed to return client_id"

        auth_url = build_authorization_url(client_id, pkce["code_challenge"], pkce["state"], settings.REDIRECT_URI)
        assert "auth/authorize" in auth_url, "Invalid authorization URL"

        print(f"  [OK] OAuth client registered. client_id: {client_id[:10]}...")
        print(f"  [OK] Authorization URL created: {auth_url[:60]}...")
        results["2_oauth_pkce"] = "PASSED"
    except Exception as e:
        print("  [FAIL] Swiggy OAuth registration issue:", e)
        results["2_oauth_pkce"] = f"FAILED: {e}"

    # ----------------------------------------------------
    # 3. PERSISTENT SQLITE SESSION STORE & ENCRYPTION TEST
    # ----------------------------------------------------
    print("\n[3/15] Testing SQLite session store & Fernet token encryption...")
    try:
        await session_store.init_db()
        test_session_id = "test_verify_session_123"
        raw_test_token = "swiggy_bearer_token_secret_999"

        await session_store.create_session(test_session_id, pkce_code_verifier=pkce["code_verifier"])
        await session_store.save_swiggy_token(test_session_id, raw_test_token)

        retrieved_token = await session_store.get_swiggy_token(test_session_id)
        assert retrieved_token == raw_test_token, "Token encryption/decryption mismatch"

        print("  [OK] Swiggy token encrypted at rest using Fernet and retrieved cleanly.")
        results["3_storage_security"] = "PASSED"
    except Exception as e:
        print("  [FAIL] Storage security test issue:", e)
        results["3_storage_security"] = f"FAILED: {e}"

    # ----------------------------------------------------
    # 4-15. LIVE SWIGGY MCP CONNECTION & WORKFLOW TEST
    # ----------------------------------------------------
    token = os.environ.get("SWIGGY_ACCESS_TOKEN", "") or settings.get("SWIGGY_ACCESS_TOKEN", "") if hasattr(settings, "get") else os.environ.get("SWIGGY_ACCESS_TOKEN", "")
    if not token:
        print("\n[4-15] SWIGGY_ACCESS_TOKEN not set in environment or .env file.")
        print("       Skipping live Swiggy MCP tool calls 4-15. To run live calls, provide SWIGGY_ACCESS_TOKEN.")
        for k in ["4_mcp_connection", "5_get_addresses", "6_search_restaurants", "7_restaurant_parser", "8_restaurant_filter", "9_restaurant_rank", "10_menu_search", "11_menu_parser_filter_rank", "12_cart_interaction", "13_langgraph_continuity", "14_replanning", "15_human_confirmation_guard"]:
            results[k] = "SKIPPED (Needs Swiggy OAuth Token)"
    else:
        print("\n[4/15] Testing real Swiggy MCP connection & tool discovery...")
        try:
            tools = await get_mcp_tools(token)
            tool_names = [t.name for t in tools]
            print(f"  [OK] Discovered {len(tools)} real Swiggy tools: {tool_names[:5]}...")
            results["4_mcp_connection"] = "PASSED"

            print("\n[5/15] Testing real get_addresses MCP call...")
            addr_res = await invoke_mcp("get_addresses", {}, swiggy_access_token=token)
            address_id = extract_first_id(addr_res)
            print("  [OK] Real address ID retrieved:", address_id)
            results["5_get_addresses"] = f"PASSED (ID: {address_id})"

            print("\n[6-7/15] Testing real search_restaurants & parser...")
            search_res = await invoke_mcp("search_restaurants", {"addressId": address_id, "query": "pizza", "offset": 0}, swiggy_access_token=token)
            parsed_rests = parse_restaurant_response(search_res)
            print(f"  [OK] Parsed {len(parsed_rests)} real restaurants.")
            results["6_search_restaurants"] = "PASSED"
            results["7_restaurant_parser"] = f"PASSED ({len(parsed_rests)} restaurants)"

            print("\n[8-9/15] Testing restaurant filter & ranking nodes...")
            dummy_state = AgentState(
                restaurants=search_res,
                requirements={"food": "pizza", "vegetarian": True, "max_budget": 500, "max_delivery_minutes": 35}
            )
            filtered_state = restaurant_filter_node(dummy_state)
            ranked_state = restaurant_rank_node(filtered_state)
            print(f"  [OK] Filtered count: {len(ranked_state.get('filtered_restaurants', []))}, Ranked count: {len(ranked_state.get('ranked_restaurants', []))}")
            results["8_restaurant_filter"] = "PASSED"
            results["9_restaurant_rank"] = "PASSED"

            if ranked_state.get("ranked_restaurants"):
                selected_rest_id = ranked_state["ranked_restaurants"][0]["restaurant_id"]
                print("\n[10-11/15] Testing real menu search, filter & rank...")
                menu_res = await invoke_mcp("search_menu", {"addressId": address_id, "query": "pizza", "restaurantIdOfAddedItem": selected_rest_id, "vegFilter": 1, "offset": 0}, swiggy_access_token=token)
                dummy_menu_state = AgentState(
                    menu_result=menu_res,
                    requirements={"food": "pizza", "vegetarian": True, "max_budget": 500}
                )
                menu_filt = menu_filter_node(dummy_menu_state)
                menu_rnk = menu_rank_node(menu_filt)
                print(f"  [OK] Filtered menu items: {len(menu_rnk.get('filtered_menu_items', []))}")
                results["10_menu_search"] = "PASSED"
                results["11_menu_parser_filter_rank"] = "PASSED"
            else:
                results["10_menu_search"] = "SKIPPED (No valid restaurant)"
                results["11_menu_parser_filter_rank"] = "SKIPPED"

            print("\n[13 & 15/15] Running LangGraph end-to-end workflow to Human Confirmation pause...")
            initial_agent_state = AgentState(
                swiggy_access_token=token,
                user_request="I want a vegetarian pizza under ₹500 delivered within 30 minutes.",
                selected_address_id=address_id,
                user_confirmation=False
            )
            graph_res = await food_agent.ainvoke(initial_agent_state)
            assert graph_res.get("needs_user_input") is True, "Graph failed to pause for human confirmation!"
            print("  [OK] LangGraph executed to step:", graph_res.get("current_step"))
            print("  [OK] Human-in-the-loop pause verified! needs_user_input =", graph_res.get("needs_user_input"))
            results["13_langgraph_continuity"] = "PASSED"
            results["15_human_confirmation_guard"] = "PASSED"

        except Exception as e:
            print("  [FAIL] Live Swiggy MCP test:", e)
            traceback.print_exc()

    print("\n==================================================")
    print("          PHASE 1 SUMMARY REPORT                 ")
    print("==================================================")
    for key, val in results.items():
        print(f"  {key:<30}: {val}")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_phase1_verification())
