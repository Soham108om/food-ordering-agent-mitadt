import asyncio

from app.agent.state import AgentState
from app.mcp.client import invoke_mcp
from app.mcp.parsers import parse_restaurant_response, restaurant_is_relevant
from app.agent.nodes.utils import notify_state_update
from app.db.memory_store import DEFAULT_WEIGHTS, memory_store


def _get_profile_sync(user_id: str) -> dict:
    """
    Read the long-term memory profile from inside a synchronous node.

    The LangGraph node is sync, so we cannot `await` directly. We run the
    async read on a fresh event loop in a worker thread to avoid interfering
    with the main event loop that is executing the graph.
    """
    import concurrent.futures

    def _runner():
        return asyncio.run(memory_store.get_profile(user_id))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_runner)
        return future.result()

async def restaurant_search_node(state: AgentState) -> AgentState:
    state["current_step"] = "SEARCH_RESTAURANTS"
    requirements = state.get("requirements", {})
    food = str(requirements.get("food", "")).strip()
    address_id = state.get("selected_address_id")
    token = state.get("swiggy_access_token")

    print("🍽️ SEARCH RESTAURANTS")
    print("Search query:", food)

    if not address_id or not token:
        print("❌ No delivery address selected or missing token.")
        state["restaurants"] = []
        state["replanning_required"] = True
        notify_state_update(state)
        return state

    try:
        result = await invoke_mcp(
            "search_restaurants",
            {
                "addressId": address_id,
                "query": food,
                "offset": 0
            },
            swiggy_access_token=token
        )
        state["restaurants"] = result
        print("✓ Real Swiggy restaurant search completed")
    except Exception as e:
        print("❌ Restaurant search failed:", type(e).__name__, str(e))
        state["restaurants"] = []
        state["replanning_required"] = True
        state["error_message"] = str(e)

    notify_state_update(state)
    return state

def restaurant_filter_node(state: AgentState) -> AgentState:
    state["current_step"] = "FILTER_RESTAURANTS"
    state["no_match_details"] = None
    print("\n🔎 FILTER RESTAURANTS")

    restaurants = parse_restaurant_response(state.get("restaurants", []))
    state["parsed_restaurants"] = restaurants

    requirements = state.get("requirements", {})
    food = str(requirements.get("food", "")).strip()
    max_delivery = requirements.get("max_delivery_minutes")

    rejection_counts = {
        "delivery_time": 0,
        "delivery_time_unavailable": 0,
        "closed": 0,
        "food_mismatch": 0
    }
    valid = []
    for restaurant in restaurants:
        name = restaurant.get("name", "Unknown")
        delivery_time = restaurant.get("delivery_minutes")
        status = str(restaurant.get("availability_status", "")).strip().upper()
        rejected = False

        if status == "CLOSED":
            rejection_counts["closed"] += 1
            rejected = True
            print(f"❌ {name}: CLOSED")

        if max_delivery is not None and delivery_time is not None and delivery_time > max_delivery:
            if delivery_time >= 999:
                rejection_counts["delivery_time_unavailable"] += 1
            else:
                rejection_counts["delivery_time"] += 1
            rejected = True
            print(f"❌ {name}: delivery time does not satisfy the requested limit")

        if not restaurant_is_relevant(restaurant, food):
            rejection_counts["food_mismatch"] += 1
            rejected = True
            print(f"❌ {name}: food relevance mismatch")

        if not rejected:
            valid.append(restaurant)

    state["filtered_restaurants"] = valid
    print("Restaurants returned:", len(restaurants))
    print("Restaurants after filter:", len(valid))

    if not valid:
        state["replanning_required"] = True
        suggestions = ["food"]
        if rejection_counts["delivery_time"]:
            suggestions.insert(0, "delivery_time")
        state["no_match_details"] = {
            "stage": "restaurants",
            "candidate_count": len(restaurants),
            "reasons": rejection_counts,
            "suggestions": suggestions
        }
        print("⚠️ No restaurant satisfies the hard constraints.")

    notify_state_update(state)
    return state

def restaurant_rank_node(state: AgentState) -> AgentState:
    state["current_step"] = "RANK_RESTAURANTS"
    restaurants = state.get("filtered_restaurants", [])

    if not restaurants:
        state["replanning_required"] = True
        print("⚠️ No restaurant satisfies the delivery hard constraint.")
        notify_state_update(state)
        return state

    # UNIT-3 FEEDBACK LOOP: use the user's LEARNED utility weights when
    # available, otherwise fall back to the fixed default weighting.
    user_id = state.get("user_id")
    weights = dict(DEFAULT_WEIGHTS)
    if user_id:
        try:
            profile = _get_profile_sync(user_id)
            weights = profile.get("weights", weights)
            print("🧠 Using learned weights from long-term memory:", weights)
        except Exception:
            pass

    budget = float(state.get("requirements", {}).get("max_budget") or 500.0)
    eta_limit = float(state.get("requirements", {}).get("max_delivery_minutes") or 30.0)

    for r in restaurants:
        price = float(r.get("price_for_two") or 0) / 2.0  # price_for_two -> approx per-item
        norm_price = max(0.0, 1.0 - (price / budget)) if budget else 0.0
        norm_eta = max(0.0, 1.0 - (float(r.get("delivery_minutes", 999)) / eta_limit)) if eta_limit else 0.0
        norm_rating = max(0.0, min(1.0, float(r.get("rating", 0)) / 5.0))
        ad_bonus = 0.02 if not r.get("is_ad") else 0.0

        r["score"] = round(
            (weights["w1"] * norm_price)
            + (weights["w2"] * norm_eta)
            + (weights["w3"] * norm_rating)
            + ad_bonus,
            4,
        )

    ranked = sorted(restaurants, key=lambda x: x["score"], reverse=True)
    state["ranked_restaurants"] = ranked

    print("🏆 RANK RESTAURANTS")
    for i, r in enumerate(ranked, 1):
        print(f"{i}. {r['name']} | {r['rating']}★ | {r['delivery_minutes']} min | score={r['score']:.3f}")

    notify_state_update(state)
    return state

def restaurant_selection_node(state: AgentState) -> AgentState:
    state["current_step"] = "SELECT_RESTAURANT"
    ranked = state.get("ranked_restaurants", [])

    if not ranked:
        state["replanning_required"] = True
        notify_state_update(state)
        return state

    selected = ranked[0]
    state["selected_restaurant"] = selected
    state["selected_restaurant_id"] = selected["restaurant_id"]
    state["needs_user_input"] = bool(state.get("allow_restaurant_selection"))

    print("👤 RESTAURANT RECOMMENDATION")
    print(f"✓ Recommended: {selected['name']}")
    print(f"✓ Rating: {selected['rating']}★")
    print(f"✓ Estimated delivery: {selected['delivery_minutes']} min")
    if state["needs_user_input"]:
        print("⏸️ Waiting for the user to confirm or change the recommended restaurant.")

    notify_state_update(state)
    return state
