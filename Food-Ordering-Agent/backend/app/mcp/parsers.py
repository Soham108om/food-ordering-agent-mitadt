import re
import json
from typing import Any, List, Dict, Optional

def extract_text(result: Any) -> str:
    """
    Extract text content recursively from MCP tool result.
    Directly extracted from notebook Cell 23.
    """
    if result is None:
        return ""

    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        if "text" in result:
            return str(result["text"])
        return "\n".join(
            extract_text(value)
            for value in result.values()
            if isinstance(value, (str, dict, list))
        )

    if isinstance(result, list):
        return "\n".join(
            extract_text(item)
            for item in result
        )

    return str(result)

def extract_first_id(result: Any) -> Optional[str]:
    """
    Extract first saved address ID or entity ID from text.
    Directly extracted from notebook Cell 24.
    """
    text = extract_text(result)
    patterns = [
        r"\(ID:\s*([A-Za-z0-9_-]+)\)",
        r'"addressId"\s*:\s*"([^"]+)"',
        r"'addressId'\s*:\s*'([^']+)'",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None

def parse_restaurant_response(result: Any) -> List[Dict[str, Any]]:
    """
    Parses raw Swiggy search_restaurants MCP response.
    Directly extracted from notebook Cell 31.
    """
    data = None

    if isinstance(result, list):
        for block in result:
            if isinstance(block, dict) and block.get("type") == "text":
                text = str(block.get("text", "")).strip()
                if not text:
                    continue
                try:
                    decoder = json.JSONDecoder()
                    data, _ = decoder.raw_decode(text)
                    if isinstance(data, dict):
                        break
                except json.JSONDecodeError:
                    continue

    elif isinstance(result, dict):
        if "restaurants" in result:
            data = result
        elif result.get("type") == "text":
            text = str(result.get("text", "")).strip()
            try:
                decoder = json.JSONDecoder()
                data, _ = decoder.raw_decode(text)
            except json.JSONDecodeError:
                data = None

    elif isinstance(result, str):
        text = result.strip()
        try:
            decoder = json.JSONDecoder()
            data, _ = decoder.raw_decode(text)
        except json.JSONDecodeError:
            data = None

    if not isinstance(data, dict):
        return []

    restaurants_raw = data.get("restaurants", [])
    if not isinstance(restaurants_raw, list):
        return []

    restaurants = []
    for r in restaurants_raw:
        if not isinstance(r, dict):
            continue

        name = str(r.get("name", "")).strip()
        restaurant_id = str(r.get("id", "")).strip()
        cuisines = r.get("cuisines", [])
        if isinstance(cuisines, list):
            cuisine_text = ", ".join(str(c) for c in cuisines)
        else:
            cuisine_text = str(cuisines)

        rating = float(r.get("avgRating") or 0)
        delivery = r.get("deliveryTimeMinutes")
        if delivery is None:
            delivery = 999

        cost_for_two = str(r.get("costForTwo", ""))
        price_match = re.search(r"₹\s*([\d,]+)", cost_for_two)
        price_for_two = (
            float(price_match.group(1).replace(",", ""))
            if price_match else None
        )

        availability = str(r.get("availabilityStatus", "")).upper()

        restaurants.append({
            "name": name.replace("(Ad)", "").strip(),
            "cuisine": cuisine_text,
            "rating": rating,
            "delivery_minutes": int(delivery),
            "price_for_two": price_for_two,
            "restaurant_id": restaurant_id,
            "area": str(r.get("areaName", "")),
            "availability_status": availability,
            "is_ad": "(Ad)" in name,
            "veg": bool(r.get("veg", False)),
            "raw": r,
        })

    return restaurants

def normalize_text(text: Optional[str]) -> str:
    """
    Normalize text for safe token matching.
    Directly extracted from notebook Cell 32.
    """
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())

def restaurant_is_relevant(restaurant: Dict[str, Any], requested_food: str) -> bool:
    """
    Determine restaurant-level food relevance.
    Directly extracted from notebook Cell 32.
    """
    requested_food = normalize_text(requested_food)
    if not requested_food:
        return True

    name = normalize_text(restaurant.get("name", ""))
    cuisine = normalize_text(restaurant.get("cuisine", ""))
    searchable = " ".join([name, cuisine])

    if requested_food in searchable:
        return True

    words = [word for word in requested_food.split() if len(word) > 2]
    if not words:
        return True

    return any(
        re.search(rf"\b{re.escape(word)}\b", searchable)
        for word in words
    )

def parse_menu_response(result: Any) -> List[Dict[str, Any]]:
    """
    Parse Swiggy search_menu MCP numbered response string.
    Directly extracted from notebook Cell 36.
    """
    items = []
    if not result:
        return items

    if isinstance(result, str):
        text = result
    elif isinstance(result, list):
        parts = []
        for block in result:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif "text" in block:
                    parts.append(str(block["text"]))
        text = "\n".join(parts)
        if not text:
            text = extract_text(result)
    elif isinstance(result, dict):
        if "text" in result:
            text = str(result["text"])
        else:
            text = extract_text(result)
    else:
        text = str(result)

    for line in text.splitlines():
        line = line.strip()
        match = re.match(r"^\s*(\d+)\.\s*(.+)$", line)
        if not match:
            continue

        item_number = int(match.group(1))
        content = match.group(2).strip()

        id_match = re.search(r"\(ID:\s*([A-Za-z0-9_-]+)\)", content, re.IGNORECASE)
        if not id_match:
            continue
        item_id = id_match.group(1)

        price_match = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", content)
        if not price_match:
            continue
        price = float(price_match.group(1).replace(",", ""))

        before_id = content[:id_match.start()]
        nonveg_match = re.search(r"\|\s*Non[-\s]?Veg\b", before_id, re.IGNORECASE)
        veg_match = re.search(r"\|\s*Veg\b", before_id, re.IGNORECASE)

        if nonveg_match:
            is_veg = False
            veg_status = "Non-Veg"
        elif veg_match:
            is_veg = True
            veg_status = "Veg"
        else:
            is_veg = False
            veg_status = "Unknown"

        name = re.split(r"\s*[—-]\s*₹", content, maxsplit=1)[0].strip()
        lower_line = line.lower()
        is_bestseller = "bestseller" in lower_line
        has_variants = "variant" in lower_line
        has_addons = "addon" in lower_line or "add-on" in lower_line

        items.append({
            "name": name,
            "price": price,
            "flags": veg_status,
            "is_veg": is_veg,
            "is_bestseller": is_bestseller,
            "has_variants": has_variants,
            "has_addons": has_addons,
            "item_id": item_id,
            "item_number": item_number,
            "raw": line
        })

    return items
