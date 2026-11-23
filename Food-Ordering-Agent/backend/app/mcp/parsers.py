import re
import json
import math
from typing import Any, List, Dict, Optional
from urllib.parse import urlparse

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

def parse_saved_addresses(result: Any) -> List[Dict[str, str]]:
    """Extract selectable saved addresses from Swiggy's formatted response."""
    text = extract_text(result)
    addresses = []
    seen_ids = set()

    for line in text.splitlines():
        id_matches = list(re.finditer(
            r"\(ID:\s*([A-Za-z0-9_-]+)\)|[\"']addressId[\"']\s*:\s*[\"']([^\"']+)[\"']",
            line,
            re.IGNORECASE
        ))
        for match in id_matches:
            address_id = match.group(1) or match.group(2)
            if address_id in seen_ids:
                continue

            preceding_text = re.sub(r"^\s*\d+[.)]\s*", "", line[:match.start()]).strip()
            label_match = re.search(r"\[([^\]]+)\]", preceding_text)
            label = label_match.group(1).strip() if label_match else f"Saved address {len(addresses) + 1}"
            details = preceding_text
            if label_match:
                details = preceding_text[label_match.end():].strip(" :-")

            addresses.append({
                "id": address_id,
                "label": label,
                "details": details
            })
            seen_ids.add(address_id)

    return addresses

def _decode_json_value(value: str) -> Any:
    try:
        decoder = json.JSONDecoder()
        decoded, _ = decoder.raw_decode(value.strip())
        return decoded
    except (json.JSONDecodeError, ValueError):
        return None

def _provider_image_url(value: Any) -> Optional[str]:
    if not isinstance(value, dict):
        return None

    image_keys = ("imageUrl", "image_url", "photoUrl", "thumbnailUrl", "image")
    for key in image_keys:
        image_url = value.get(key)
        if not isinstance(image_url, str):
            continue

        image_url = image_url.strip()
        try:
            parsed = urlparse(image_url)
        except ValueError:
            continue
        hostname = (parsed.hostname or "").lower()
        if (
            parsed.scheme == "https"
            and not parsed.username
            and not parsed.password
            and (hostname == "swiggy.com" or hostname.endswith(".swiggy.com"))
        ):
            return image_url

    return None

def _tracking_objects(value: Any):
    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str):
            decoded = _decode_json_value(text)
            if decoded is not None:
                yield from _tracking_objects(decoded)
        yield value
        for child in value.values():
            yield from _tracking_objects(child)
    elif isinstance(value, list):
        for item in value:
            yield from _tracking_objects(item)
    elif isinstance(value, str):
        decoded = _decode_json_value(value)
        if decoded is not None:
            yield from _tracking_objects(decoded)

def parse_order_tracking(result: Any) -> Dict[str, Optional[str]]:
    """Extract explicit provider tracking status, ETA, and message fields."""
    status_keys = (
        "orderstatus", "deliverystatus", "trackingstatus", "currentstatus"
    )
    eta_keys = (
        "eta", "estimateddeliverytime", "estimatedarrivaltime",
        "expecteddeliverytime", "deliveryeta"
    )
    minute_eta_keys = ("estimateddeliveryminutes", "etaminutes")
    message_keys = ("statusmessage", "trackingmessage", "description", "message")
    summary: Dict[str, Optional[str]] = {
        "status": None,
        "estimated_delivery": None,
        "message": None
    }
    generic_status = None

    def text_value(value: Any) -> Optional[str]:
        if isinstance(value, str):
            return value.strip() or None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        return None

    for candidate in _tracking_objects(result):
        normalized = {
            re.sub(r"[^a-z0-9]", "", str(key).lower()): value
            for key, value in candidate.items()
        }
        if summary["status"] is None:
            for key in status_keys:
                summary["status"] = text_value(normalized.get(key))
                if summary["status"]:
                    break
        if generic_status is None:
            candidate_status = text_value(normalized.get("status"))
            if candidate_status and candidate_status.casefold() not in {"success", "ok", "error"}:
                generic_status = candidate_status
        if summary["estimated_delivery"] is None:
            for key in eta_keys:
                summary["estimated_delivery"] = text_value(normalized.get(key))
                if summary["estimated_delivery"]:
                    break
            if summary["estimated_delivery"] is None:
                for key in minute_eta_keys:
                    minutes = text_value(normalized.get(key))
                    if minutes:
                        summary["estimated_delivery"] = f"{minutes} min"
                        break
        if summary["message"] is None:
            for key in message_keys:
                summary["message"] = text_value(normalized.get(key))
                if summary["message"]:
                    break
        if all(summary.values()):
            break

    if summary["status"] is None:
        summary["status"] = generic_status

    text = extract_text(result)
    if summary["status"] is None:
        status_match = re.search(
            r"(?:order|delivery|tracking)\s+status\s*[:=]\s*([^\r\n,;]+)",
            text,
            re.IGNORECASE
        )
        if status_match:
            summary["status"] = status_match.group(1).strip()
    if summary["estimated_delivery"] is None:
        eta_match = re.search(
            r"(?:estimated\s+delivery(?:\s+time)?|expected\s+delivery|ETA)\s*[:=]\s*([^\r\n,;]+)",
            text,
            re.IGNORECASE
        )
        if eta_match:
            summary["estimated_delivery"] = eta_match.group(1).strip()

    return summary

def _pricing_objects(value: Any):
    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str):
            decoded = _decode_json_value(text)
            if decoded is not None:
                yield from _pricing_objects(decoded)

        yield value
        ignored_lists = {"items", "cartitems", "lineitems", "itemdetails"}
        for key, child in value.items():
            if str(key).lower().replace("_", "") in ignored_lists:
                continue
            yield from _pricing_objects(child)
    elif isinstance(value, list):
        for item in value:
            yield from _pricing_objects(item)
    elif isinstance(value, str):
        decoded = _decode_json_value(value)
        if decoded is not None:
            yield from _pricing_objects(decoded)

def _money_value(value: Any) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        amount = float(value)
        return amount if math.isfinite(amount) else None
    match = re.search(r"-?\d[\d,]*(?:\.\d{1,2})?", str(value))
    if not match:
        return None
    return float(match.group(0).replace(",", ""))

def parse_cart_pricing(result: Any) -> Dict[str, Any]:
    """Extract only explicit price totals and charges from a live cart response."""
    total_keys = (
        "grandtotal", "totalamount", "amountpayable", "payableamount",
        "carttotal", "totalpayable", "netamount", "billamount", "total"
    )
    subtotal_keys = (
        "itemtotal", "itemsubtotal", "itemssubtotal", "foodtotal", "subtotal"
    )
    charge_keys = {
        "deliverycharge": "Delivery fee",
        "deliverycharges": "Delivery fee",
        "deliveryfee": "Delivery fee",
        "packagingcharge": "Packaging fee",
        "packagingfee": "Packaging fee",
        "packingcharge": "Packaging fee",
        "packingfee": "Packaging fee",
        "platformfee": "Platform fee",
        "conveniencefee": "Convenience fee",
        "tax": "Tax",
        "taxes": "Tax",
        "gst": "GST"
    }

    for candidate in _pricing_objects(result):
        normalized = {
            re.sub(r"[^a-z0-9]", "", str(key).lower()): value
            for key, value in candidate.items()
        }

        def find_amount(keys):
            for key in keys:
                if key in normalized:
                    amount = _money_value(normalized[key])
                    if amount is not None:
                        return amount
            return None

        total = find_amount(total_keys)
        subtotal = find_amount(subtotal_keys)
        charges = []
        seen_labels = set()
        for key, label in charge_keys.items():
            amount = _money_value(normalized.get(key))
            if amount is not None and label not in seen_labels:
                charges.append({"label": label, "amount": amount})
                seen_labels.add(label)

        if total is not None or subtotal is not None or charges:
            return {
                "total_amount": total,
                "item_subtotal": subtotal,
                "charges": charges
            }

    text = extract_text(result)
    total_match = re.search(
        r"(?:grand\s+total|cart\s+total|amount\s+payable|total\s+amount)\s*(?:is|:|=)?\s*(?:₹|INR\s*)?([\d,]+(?:\.\d{1,2})?)",
        text,
        re.IGNORECASE
    )
    return {
        "total_amount": _money_value(total_match.group(1)) if total_match else None,
        "item_subtotal": None,
        "charges": []
    }

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
            "image_url": _provider_image_url(r),
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
        rating_match = re.search(
            r"\|\s*(\d+(?:\.\d+)?)\s*★(?:\s*\((\d+)\))?",
            before_id
        )

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
        serving_match = re.search(r"\[([^\]]+)\]\s*$", name)
        serving_label = serving_match.group(1).strip() if serving_match else None
        if serving_match:
            name = name[:serving_match.start()].strip()
        lower_line = line.lower()
        is_bestseller = "bestseller" in lower_line
        has_variants = "variant" in lower_line
        has_addons = "addon" in lower_line or "add-on" in lower_line
        image_match = re.search(
            r"(?:image(?:\s+url)?|photo(?:\s+url)?|thumbnail(?:\s+url)?)\s*[:=]\s*(https://[^\s)\]]+)",
            content,
            re.IGNORECASE
        )
        image_url = _provider_image_url({
            "imageUrl": image_match.group(1).rstrip(".,")
        }) if image_match else None

        items.append({
            "name": name,
            "price": price,
            "flags": veg_status,
            "is_veg": is_veg,
            "is_bestseller": is_bestseller,
            "rating": float(rating_match.group(1)) if rating_match else None,
            "rating_count": int(rating_match.group(2)) if rating_match and rating_match.group(2) else None,
            "serving_label": serving_label,
            "has_variants": has_variants,
            "has_addons": has_addons,
            "image_url": image_url,
            "item_id": item_id,
            "item_number": item_number,
            "raw": line
        })

    return items
