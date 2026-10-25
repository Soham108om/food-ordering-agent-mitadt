from app.agent.state import AgentState
from app.mcp.client import invoke_mcp
from app.mcp.parsers import parse_restaurant_response, restaurant_is_relevant
from app.agent.nodes.utils import notify_state_update

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
    print("\n🔎 FILTER RESTAURANTS")

    restaurants = parse_restaurant_response(state.get("restaurants", []))
    state["parsed_restaurants"] = restaurants

    requirements = state.get("requirements", {})
    food = str(requirements.get("food", "")).strip()
    max_delivery = requirements.get("max_delivery_minutes")

    valid = []
    for restaurant in restaurants:
        name = restaurant.get("name", "Unknown")
        delivery_time = restaurant.get("delivery_minutes")
        status = str(restaurant.get("availability_status", "")).strip().upper()

        if max_delivery is not None and delivery_time is not None and delivery_time > max_delivery:
            print(f"❌ {name}: {delivery_time} min > {max_delivery} min")
            continue

        if status == "CLOSED":
            print(f"❌ {name}: CLOSED")
            continue

        if not restaurant_is_relevant(restaurant, food):
            print(f"❌ {name}: food relevance mismatch")
            continue

        valid.append(restaurant)

    state["filtered_restaurants"] = valid
    print("Restaurants returned:", len(restaurants))
    print("Restaurants after filter:", len(valid))

    if not valid:
        state["replanning_required"] = True
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

    for r in restaurants:
        r["score"] = (
            r["rating"] * 20
            + max(0, 50 - r["delivery_minutes"])
            + (2 if not r["is_ad"] else 0)
        )

    ranked = sorted(restaurants, key=lambda x: x["score"], reverse=True)
    state["ranked_restaurants"] = ranked

    print("🏆 RANK RESTAURANTS")
    for i, r in enumerate(ranked, 1):
        print(f"{i}. {r['name']} | {r['rating']}★ | {r['delivery_minutes']} min | score={r['score']:.1f}")

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

    print("👤 RESTAURANT RECOMMENDATION")
    print(f"✓ Recommended: {selected['name']}")
    print(f"✓ Rating: {selected['rating']}★")
    print(f"✓ Estimated delivery: {selected['delivery_minutes']} min")

    notify_state_update(state)
    return state
