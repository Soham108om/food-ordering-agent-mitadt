from langgraph.graph import StateGraph, END
from app.agent.state import AgentState

from app.agent.nodes.understand import understand_node
from app.agent.nodes.plan import plan_node
from app.agent.nodes.restaurant import (
    restaurant_search_node,
    restaurant_filter_node,
    restaurant_rank_node,
    restaurant_selection_node
)
from app.agent.nodes.menu import (
    menu_node,
    menu_filter_node,
    menu_rank_node,
    item_selection_node
)
from app.agent.nodes.customization import customization_node
from app.agent.nodes.cart import cart_node
from app.agent.nodes.payment import payment_node
from app.agent.nodes.order import order_node
from app.agent.nodes.tracking import tracking_node
from app.agent.nodes.replan import replan_node

from app.agent.routing import (
    route_after_restaurant_rank,
    route_after_menu_rank,
    route_after_cart,
    route_after_payment,
    route_after_order
)

def build_food_agent_graph():
    """
    Assembles the exact StateGraph directly extracted from notebook Cell 55.
    """
    builder = StateGraph(AgentState)

    # Core Nodes
    builder.add_node("understand", understand_node)
    builder.add_node("plan", plan_node)

    # Restaurant Pipeline
    builder.add_node("restaurant_search", restaurant_search_node)
    builder.add_node("restaurant_filter", restaurant_filter_node)
    builder.add_node("restaurant_rank", restaurant_rank_node)
    builder.add_node("restaurant_selection", restaurant_selection_node)

    # Menu Pipeline
    builder.add_node("menu", menu_node)
    builder.add_node("menu_filter", menu_filter_node)
    builder.add_node("menu_rank", menu_rank_node)
    builder.add_node("item_selection", item_selection_node)

    # Customization & Cart
    builder.add_node("customization", customization_node)
    builder.add_node("cart", cart_node)

    # Payment & Order
    builder.add_node("payment", payment_node)
    builder.add_node("order", order_node)
    builder.add_node("tracking", tracking_node)

    # Replan
    builder.add_node("replan", replan_node)

    # Entry point
    builder.set_entry_point("understand")

    # Main Edges
    builder.add_edge("understand", "plan")
    builder.add_edge("plan", "restaurant_search")
    builder.add_edge("restaurant_search", "restaurant_filter")
    builder.add_edge("restaurant_filter", "restaurant_rank")

    # Restaurant Rank Router
    builder.add_conditional_edges(
        "restaurant_rank",
        route_after_restaurant_rank,
        {
            "continue": "restaurant_selection",
            "replan": "replan"
        }
    )
    builder.add_edge("restaurant_selection", "menu")

    # Menu Pipeline Edges
    builder.add_edge("menu", "menu_filter")
    builder.add_edge("menu_filter", "menu_rank")

    # Menu Rank Router
    builder.add_conditional_edges(
        "menu_rank",
        route_after_menu_rank,
        {
            "continue": "item_selection",
            "replan": "replan"
        }
    )
    builder.add_edge("item_selection", "customization")
    builder.add_edge("customization", "cart")

    # Cart Router
    builder.add_conditional_edges(
        "cart",
        route_after_cart,
        {
            "waiting": END,
            "replan": "replan",
            "payment": "payment"
        }
    )

    # Payment Router
    builder.add_conditional_edges(
        "payment",
        route_after_payment,
        {
            "waiting": END,
            "order": "order"
        }
    )

    # Order Router
    builder.add_conditional_edges(
        "order",
        route_after_order,
        {
            "tracking": "tracking",
            "end": END
        }
    )

    builder.add_edge("tracking", END)
    builder.add_edge("replan", END)

    return builder.compile()

food_agent = build_food_agent_graph()
