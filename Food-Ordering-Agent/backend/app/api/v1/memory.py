"""
UNIT-3 DEMO MODULE: API surface for Long-Term Memory + Feedback Loop

Endpoints:
    GET  /api/v1/memory/{user_id}          -> long-term profile + learned weights
    GET  /api/v1/memory/{user_id}/history  -> auditable feedback log
    POST /api/v1/memory/{user_id}/feedback -> record accept/reject, update weights
    POST /api/v1/memory/{user_id}/reset    -> cold-start reset
    GET  /api/v1/memory/demo/weights       -> the current utility function
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.memory_store import (
    DEFAULT_WEIGHTS,
    LEARNING_RATE,
    memory_store,
    normalise_attributes,
    update_weights,
)

router = APIRouter(prefix="/memory", tags=["Long-Term Memory & Feedback Loop"])


class FeedbackRequest(BaseModel):
    accepted: bool
    session_id: Optional[str] = None
    target_type: str = "menu_item"
    target_name: Optional[str] = None
    reason: Optional[str] = None
    price: Optional[float] = None
    eta: Optional[float] = None
    rating: Optional[float] = None


@router.get("/demo/weights")
async def get_weight_spec():
    """
    Expose the learning configuration so the demo can show exactly what is
    being learned and how fast.
    """
    return {
        "utility_function": (
            "U(x) = w1*(1 - Price/Budget) + w2*(1 - ETA/EtaLimit) "
            "+ w3*(Rating/RatingMax) + beta_pop*Popularity"
        ),
        "dimensions": {
            "w1": "price sensitivity (lower cost is better)",
            "w2": "speed sensitivity (shorter ETA is better)",
            "w3": "quality sensitivity (higher rating is better)",
        },
        "cold_start_weights": DEFAULT_WEIGHTS,
        "learning_rate": LEARNING_RATE,
        "update_rule": (
            "accept -> reinforce the strongest dimension, damp the weakest; "
            "reject -> boost the weakest dimension (the one we under-weighted), "
            "damp the strongest. Weights are clamped and renormalised to sum=1."
        ),
    }


@router.get("/{user_id}")
async def get_profile(user_id: str):
    """
    Long-term memory read: the durable profile for a user.

    This is what survives a backend restart, and what a *new* session for the
    same user will automatically pick up.
    """
    profile = await memory_store.get_profile(user_id)
    history = await memory_store.get_feedback_history(user_id, limit=10)
    return {
        "user_id": user_id,
        "weights": profile["weights"],
        "preferences": profile.get("preferences") or {},
        "interaction_count": profile.get("interaction_count", 0),
        "accept_count": profile.get("accept_count", 0),
        "reject_count": profile.get("reject_count", 0),
        "cold_start": profile.get("cold_start", False),
        "recent_feedback": history,
        "created_at": profile.get("created_at"),
        "updated_at": profile.get("updated_at"),
    }


@router.get("/{user_id}/history")
async def get_history(user_id: str, limit: int = 25):
    """Full audit trail of feedback events with before/after weight vectors."""
    rows = await memory_store.get_feedback_history(user_id, limit=limit)
    return {"user_id": user_id, "count": len(rows), "events": rows}


@router.post("/{user_id}/feedback")
async def record_feedback(user_id: str, payload: FeedbackRequest):
    """
    THE FEEDBACK LOOP ENDPOINT.

    Records an explicit human judgement, performs one online weight update,
    and persists both the new weights and the audit row. The next ranking
    performed for this user will use the updated weights.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    result = await memory_store.record_feedback(
        user_id=user_id,
        accepted=payload.accepted,
        session_id=payload.session_id,
        target_type=payload.target_type,
        target_name=payload.target_name,
        reason=payload.reason,
        price=payload.price,
        eta=payload.eta,
        rating=payload.rating,
    )
    return result


@router.post("/{user_id}/reset")
async def reset_user(user_id: str):
    """Forget a user entirely, to demonstrate cold-start behaviour."""
    await memory_store.reset_user(user_id)
    return {"user_id": user_id, "status": "reset", "weights": DEFAULT_WEIGHTS}


@router.post("/{user_id}/observe")
async def observe_request(user_id: str, requirements: Dict[str, Any]):
    """
    Passive part of the feedback loop: distil a stated requirement into the
    durable preference profile so later sessions inherit it.
    """
    result = await memory_store.observe_request(user_id, requirements)
    profile = await memory_store.get_profile(user_id)
    return {
        "user_id": user_id,
        "preferences": result["preferences"],
        "weights": profile["weights"],
    }
