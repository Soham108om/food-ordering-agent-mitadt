from typing import TypedDict, Any, Optional, Dict, List

class AgentState(TypedDict, total=False):
    session_id: Optional[str]
    swiggy_access_token: Optional[str]

    user_request: str
    requirements: dict
    cuisine: Optional[str]
    food_components: Optional[List[str]]

    addresses: Any
    selected_address_id: Optional[str]

    restaurants: Any
    parsed_restaurants: list
    filtered_restaurants: list
    ranked_restaurants: list
    selected_restaurant: dict
    selected_restaurant_id: Optional[str]

    menu_result: Any
    menu_options: list
    filtered_menu_items: list
    ranked_menu_items: list
    selected_item: dict

    customization_result: Any
    selected_customization: dict

    cart_result: Any
    cart: Any

    payment_options: Any
    payment_method: Optional[str]
    intent_app: Optional[str]
    generate_upi_qr: Optional[bool]

    user_confirmation: bool

    order_result: Any
    order_id: Optional[str]
    order_status: Optional[str]
    payment_status_result: Any

    tracking_result: Any

    current_step: str
    needs_user_input: bool
    replanning_required: bool
    error_message: Optional[str]
