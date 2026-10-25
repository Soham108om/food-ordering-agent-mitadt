import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.agent.state import AgentState
from app.mcp.client import invoke_mcp
from app.mcp.parsers import parse_menu_response
from app.agent.nodes.utils import notify_state_update

def is_core_food_item(item_name: str, food_query: str) -> bool:
    """
    Determines if an item name represents the primary requested dish 
    versus a secondary snack, side, dip, or bread modifier.
    """
    name_lower = item_name.lower()
    query_lower = food_query.lower().strip()

    if not query_lower:
        return True

    side_modifiers = [
        "puff", "puffs", "pocket", "pockets", "side", "sides", "bread", "breads",
        "garlic bread", "dip", "dips", "wrap", "wraps", "roll", "rolls", "fries",
        "taco", "tacos", "calzone", "slider", "beverage", "drink", "shake", "dessert"
    ]

    has_modifier = any(
        re.search(rf"\b{re.escape(mod)}\b", name_lower)
        for mod in side_modifiers
        if mod != query_lower
    )
    has_query = bool(re.search(rf"\b{re.escape(query_lower)}\b", name_lower))

    return has_query and not has_modifier

async def menu_node(state: AgentState) -> AgentState:
    state["current_step"] = "SEARCH_MENU"
    restaurant_id = state.get("selected_restaurant_id")
    address_id = state.get("selected_address_id")
    token = state.get("swiggy_access_token")
    requirements = state.get("requirements", {})

    food = str(requirements.get("food", "")).strip()
    food_components = state.get("food_components") or requirements.get("food_components") or []
    vegetarian = bool(requirements.get("vegetarian", False))

    # Pick clean search query keyword
    search_query = food
    if not search_query and food_components:
        search_query = food_components[0]
    if not search_query:
        search_query = "meal"

    print("\n🍕 SEARCH MENU")
    print("Restaurant ID:", restaurant_id)
    print("Search query:", search_query)

    if not restaurant_id or not address_id or not token:
        print("❌ Missing restaurant ID, address ID, or token.")
        state["menu_result"] = []
        state["replanning_required"] = True
        notify_state_update(state)
        return state

    try:
        result = await invoke_mcp(
            "search_menu",
            {
                "addressId": address_id,
                "query": search_query,
                "restaurantIdOfAddedItem": str(restaurant_id),
                "vegFilter": 1 if vegetarian else 0,
                "offset": 0
            },
            swiggy_access_token=token
        )
        parsed_items = parse_menu_response(result)

        # Intelligent Fallback: If 0 items parsed and secondary components exist, try searching component term
        if not parsed_items and food_components and len(food_components) > 1:
            fallback_query = food_components[1]
            print(f"🔄 Retrying menu search with component: '{fallback_query}'...")
            result = await invoke_mcp(
                "search_menu",
                {
                    "addressId": address_id,
                    "query": fallback_query,
                    "restaurantIdOfAddedItem": str(restaurant_id),
                    "vegFilter": 1 if vegetarian else 0,
                    "offset": 0
                },
                swiggy_access_token=token
            )
            parsed_items = parse_menu_response(result)

        state["menu_result"] = result
        state["menu_options"] = parsed_items
        print("✓ Real Swiggy menu search completed. Parsed items:", len(parsed_items))

        if not parsed_items:
            print("⚠️ No menu items could be parsed.")
            state["replanning_required"] = True

    except Exception as e:
        print("❌ Menu search failed:", type(e).__name__, str(e))
        state["menu_result"] = []
        state["menu_options"] = []
        state["replanning_required"] = True
        state["error_message"] = str(e)

    notify_state_update(state)
    return state

def menu_filter_node(state: AgentState) -> AgentState:
    state["current_step"] = "FILTER_MENU"
    print("\n🔎 FILTER MENU")

    items = state.get("menu_options", [])
    if not items:
        items = parse_menu_response(state.get("menu_result", []))

    requirements = state.get("requirements", {})
    food = str(requirements.get("food", "")).strip().lower()
    food_components = [c.lower().strip() for c in (state.get("food_components") or requirements.get("food_components") or [])]
    cuisine = str(state.get("cuisine") or requirements.get("cuisine") or "").lower().strip()
    vegetarian = bool(requirements.get("vegetarian", False))
    max_budget = requirements.get("max_budget")

    # Combine search terms for flexible compound matching
    all_search_terms = set(food_components)
    if food:
        all_search_terms.add(food)
    if cuisine:
        all_search_terms.add(cuisine)
    all_search_terms.discard("")

    valid = []
    for item in items:
        item_name = str(item.get("name", "")).lower()

        # Item relevance: Matches any requested component, cuisine, or main food term
        if all_search_terms:
            matches_term = any(
                re.search(rf"\b{re.escape(term)}\b", item_name)
                for term in all_search_terms
            )
            # Also match thalis, meals, or combos if compound food requested
            matches_combo = any(w in item_name for w in ["thali", "combo", "meal", "platter", "special"])
            if not (matches_term or matches_combo):
                continue

        # Vegetarian Hard Constraint
        if vegetarian and not item.get("is_veg", False):
            continue

        # Budget Hard Constraint (applied to individual item price)
        price = item.get("price", float("inf"))
        if max_budget is not None and price > max_budget:
            print(f"❌ {item.get('name')}: ₹{price} > ₹{max_budget}")
            continue

        valid.append(item)

    # Deduplicate by item_id
    unique = {}
    for item in valid:
        item_id = item.get("item_id")
        if item_id:
            unique[item_id] = item

    filtered = list(unique.values())
    state["filtered_menu_items"] = filtered

    print("Menu items found:", len(items))
    print("Valid menu items:", len(filtered))

    if not filtered:
        state["replanning_required"] = True
        print("⚠️ No menu item satisfies all hard constraints.")
    else:
        state["replanning_required"] = False

    notify_state_update(state)
    return state

def menu_rank_node(state: AgentState) -> AgentState:
    state["current_step"] = "RANK_MENU"
    items = state.get("filtered_menu_items", [])
    requirements = state.get("requirements", {})
    food = str(requirements.get("food", "")).strip()
    food_components = [c.lower().strip() for c in (state.get("food_components") or requirements.get("food_components") or [])]

    if not items:
        state["replanning_required"] = True
        print("⚠️ No menu item satisfies constraints.")
        notify_state_update(state)
        return state

    for item in items:
        item_name = str(item.get("name", "")).lower()

        # Semantic Relevance Scoring for Compound & Single Requests
        relevance_score = 0
        if food_components:
            matched_components = sum(1 for c in food_components if re.search(rf"\b{re.escape(c)}\b", item_name))
            is_combo = any(w in item_name for w in ["thali", "combo", "meal", "platter", "special"])

            if matched_components >= 2 or (matched_components >= 1 and is_combo):
                relevance_score = 150  # Multiple components or combo meal
            elif matched_components >= 1:
                relevance_score = 100  # Primary component match
            elif is_combo:
                relevance_score = 75   # General thali/meal
        else:
            if is_core_food_item(item["name"], food):
                relevance_score = 100

        # Secondary soft preference factors
        bestseller_bonus = 20 if item.get("is_bestseller") else 0
        variant_bonus = 5 if (item.get("has_variants") or item.get("has_addons")) else 0
        price_value_score = max(0, 50 - item.get("price", 0) / 20)

        total_score = relevance_score + bestseller_bonus + variant_bonus + price_value_score
        item["score"] = round(total_score, 2)

    ranked = sorted(items, key=lambda x: x["score"], reverse=True)
    state["ranked_menu_items"] = ranked

    print("🏆 RANK MENU")
    for i, item in enumerate(ranked[:10], 1):
        print(f"{i}. {item['name']} | ₹{item['price']:.0f} | score={item['score']}")

    notify_state_update(state)
    return state

def item_selection_node(state: AgentState) -> AgentState:
    state["current_step"] = "SELECT_ITEM"
    ranked = state.get("ranked_menu_items", [])

    if not ranked:
        state["replanning_required"] = True
        notify_state_update(state)
        return state

    selected = ranked[0]
    state["selected_item"] = selected

    print("👤 SELECT ITEM")
    print("✓", selected["name"])
    print("✓ Price: ₹", selected["price"])

    notify_state_update(state)
    return state
