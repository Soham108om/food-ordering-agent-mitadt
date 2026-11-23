"""
UNIT-3 DEMO MODULE: Long-Term User Memory + Adaptive Feedback Loop

Core Concepts Demonstrated:
  1. LONG MEMORY  - Cross-session persistence of user preferences and learned
                     parameters in SQLite. Memory survives process restarts and
                     is keyed by a stable user identifier, not a session id.
  2. FEEDBACK LOOP - Human feedback (accept / reject) is captured as a training
                     signal and fed back into the ranking policy via a
                     contextual-bandit style online weight update. The updated
                     weights are applied on the *next* inference.

The multi-attribute utility function used for ranking is:

    U(x) = w1 * (1 - Price(x)/Budget)
         + w2 * (1 - ETA(x)/EtaLimit)
         + w3 * (Rating(x)/RatingMax)
         + beta_pop * Popularity(x)

where (w1, w2, w3) are LEARNED from user feedback rather than hard-coded.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

from app.core.config import settings


# ---------------------------------------------------------------------------
# Learning hyper-parameters
# ---------------------------------------------------------------------------

#: Initial (cold-start) utility weights: price, speed, quality.
DEFAULT_WEIGHTS: Dict[str, float] = {"w1": 0.35, "w2": 0.40, "w3": 0.25}

#: Per-feedback-step learning rate.
LEARNING_RATE: float = 0.05

#: Each weight is clamped to this closed interval before renormalisation.
WEIGHT_BOUNDS: Tuple[float, float] = (0.10, 0.70)

#: Normalisation ceilings used when converting raw attributes to [0, 1] units.
BUDGET_CEILING: float = 500.0
ETA_CEILING: float = 30.0
RATING_CEILING: float = 5.0

#: How many recent interactions are kept in the rolling preference profile.
PROFILE_WINDOW: int = 20


def _clamp(value: float) -> float:
    return max(WEIGHT_BOUNDS[0], min(WEIGHT_BOUNDS[1], value))


def _renormalise(weights: Dict[str, float]) -> Dict[str, float]:
    """Project weights back onto the probability simplex (sum == 1)."""
    clamped = {k: _clamp(v) for k, v in weights.items()}
    total = sum(clamped.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: round(v / total, 4) for k, v in clamped.items()}


def normalise_attributes(
    price: Optional[float],
    eta: Optional[float],
    rating: Optional[float],
) -> Dict[str, float]:
    """
    Convert raw item attributes into comparable units in [0, 1].

    Higher value == better on that dimension. Price and ETA are inverted so
    that "cheap" and "fast" both score high, matching the utility function.
    """
    p = 0.0 if price is None else max(0.0, 1.0 - (float(price) / BUDGET_CEILING))
    e = 0.0 if eta is None else max(0.0, 1.0 - (float(eta) / ETA_CEILING))
    r = 0.0 if rating is None else max(0.0, min(1.0, float(rating) / RATING_CEILING))
    return {"w1": round(p, 4), "w2": round(e, 4), "w3": round(r, 4)}


def update_weights(
    weights: Dict[str, float],
    accepted: bool,
    attributes: Dict[str, float],
) -> Dict[str, float]:
    """
    Contextual-bandit style online weight update driven by human feedback.

    Rule:
      * ACCEPTED  -> reinforce the dimension on which the chosen item was
        strongest (the user liked it, so that attribute mattered), and damp the
        dimension on which it was weakest.
      * REJECTED  -> the agent under-weighted the dimension on which the chosen
        item was weakest (that is why the user said no). Boost that dimension
        and damp the strongest one, which the agent had over-valued.

    The update is applied as a small gradient step and then clamped and
    renormalised so the weights stay a valid convex combination.
    """
    base = {k: float(weights.get(k, DEFAULT_WEIGHTS[k])) for k in ("w1", "w2", "w3")}

    if not attributes:
        return _renormalise(base)

    scored = {k: float(attributes.get(k, 0.0)) for k in ("w1", "w2", "w3")}
    strongest = max(scored, key=lambda k: scored[k])
    weakest = min(scored, key=lambda k: scored[k])

    if accepted:
        target, damp = strongest, weakest
    else:
        target, damp = weakest, strongest

    updated = dict(base)
    updated[target] = updated[target] + LEARNING_RATE
    updated[damp] = updated[damp] - (LEARNING_RATE * 0.5)

    return _renormalise(updated)


class UserMemoryStore:
    """
    Long-term memory store for a single user.

    Unlike `SessionStore` (which holds the live, in-flight agent state for one
    conversation), this store holds durable knowledge that accumulates across
    sessions:

      * `user_memory`   - the distilled profile: learned weights + counters.
      * `feedback_log`  - an append-only audit trail of every feedback event,
                          including the weight vector before and after the
                          update (needed to show the learning is real).

    Both tables live in the same SQLite file as the session store, so the
    whole system still runs from one file.
    """

    def __init__(self, db_path: str = settings.DATABASE_PATH):
        self.db_path = db_path

    # -- schema ------------------------------------------------------------

    async def init_db(self) -> None:
        """Create the long-term memory tables if they do not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT PRIMARY KEY,
                    w1 REAL NOT NULL DEFAULT 0.35,
                    w2 REAL NOT NULL DEFAULT 0.40,
                    w3 REAL NOT NULL DEFAULT 0.25,
                    interaction_count INTEGER DEFAULT 0,
                    accept_count INTEGER DEFAULT 0,
                    reject_count INTEGER DEFAULT 0,
                    preferences_json TEXT,
                    history_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    target_type TEXT,
                    target_name TEXT,
                    accepted INTEGER NOT NULL,
                    reason TEXT,
                    attributes_json TEXT,
                    weights_before_json TEXT,
                    weights_after_json TEXT,
                    created_at TEXT
                )
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_feedback_user
                ON feedback_log(user_id, created_at DESC)
                """
            )
            await db.commit()

    # -- reads -------------------------------------------------------------

    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Return the durable profile for a user: learned weights, counters and
        the rolling preference history. Creates a cold-start profile if the
        user is seen for the first time.
        """
        if not user_id:
            return {
                "user_id": user_id,
                "weights": dict(DEFAULT_WEIGHTS),
                "preferences": {},
                "history": [],
                "interaction_count": 0,
                "accept_count": 0,
                "reject_count": 0,
                "cold_start": True,
            }

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM user_memory WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                # First encounter: persist the cold-start profile.
                now = datetime.utcnow().isoformat()
                await db.execute(
                    """
                    INSERT INTO user_memory
                    (user_id, w1, w2, w3, interaction_count, accept_count, reject_count,
                     preferences_json, history_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, 0, 0, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        DEFAULT_WEIGHTS["w1"],
                        DEFAULT_WEIGHTS["w2"],
                        DEFAULT_WEIGHTS["w3"],
                        json.dumps({}),
                        json.dumps([]),
                        now,
                        now,
                    ),
                )
                await db.commit()
                return {
                    "user_id": user_id,
                    "weights": dict(DEFAULT_WEIGHTS),
                    "preferences": {},
                    "history": [],
                    "interaction_count": 0,
                    "accept_count": 0,
                    "reject_count": 0,
                    "cold_start": True,
                }

            data = dict(row)
            return {
                "user_id": data["user_id"],
                "weights": {
                    "w1": round(float(data["w1"]), 4),
                    "w2": round(float(data["w2"]), 4),
                    "w3": round(float(data["w3"]), 4),
                },
                "preferences": json.loads(data.get("preferences_json") or "{}"),
                "history": json.loads(data.get("history_json") or "[]"),
                "interaction_count": int(data.get("interaction_count") or 0),
                "accept_count": int(data.get("accept_count") or 0),
                "reject_count": int(data.get("reject_count") or 0),
                "cold_start": False,
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
            }

    async def get_feedback_history(self, user_id: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Return the most recent feedback events, newest first."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM feedback_log WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()

        return [
            {
                "id": r["id"],
                "target_type": r["target_type"],
                "target_name": r["target_name"],
                "accepted": bool(r["accepted"]),
                "reason": r["reason"],
                "attributes": json.loads(r["attributes_json"] or "{}"),
                "weights_before": json.loads(r["weights_before_json"] or "{}"),
                "weights_after": json.loads(r["weights_after_json"] or "{}"),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # -- writes ------------------------------------------------------------

    async def observe_request(
        self,
        user_id: str,
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Record a *request* (not yet a decision) into the rolling profile.

        This is the passive part of the feedback loop: the agent observes the
        user stating a preference ("vegetarian", "under 400") and stores it, so
        that a later session can pre-apply it even if the user forgets to
        restate it.
        """
        profile = await self.get_profile(user_id)
        preferences: Dict[str, Any] = dict(profile.get("preferences") or {})

        for key in ("vegetarian", "cuisine", "max_budget", "max_delivery_minutes"):
            value = requirements.get(key)
            if value is None or value == "":
                continue
            if key == "max_budget":
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue
                previous = preferences.get(key)
                # Keep the tightest budget the user has ever stated.
                if previous is None or value < float(previous):
                    preferences[key] = value
            elif key == "max_delivery_minutes":
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    continue
                previous = preferences.get(key)
                if previous is None or value < int(previous):
                    preferences[key] = value
            else:
                preferences[key] = value

        history: List[Dict[str, Any]] = list(profile.get("history") or [])
        history.append({
            "kind": "request",
            "requirements": requirements,
            "at": datetime.utcnow().isoformat(),
        })
        history = history[-PROFILE_WINDOW:]

        await self._persist_profile(
            user_id=user_id,
            weights=profile["weights"],
            preferences=preferences,
            history=history,
            interaction_count=profile.get("interaction_count", 0),
            accept_count=profile.get("accept_count", 0),
            reject_count=profile.get("reject_count", 0),
        )
        return {"preferences": preferences, "history_len": len(history)}

    async def record_feedback(
        self,
        user_id: str,
        accepted: bool,
        session_id: Optional[str] = None,
        target_type: str = "menu_item",
        target_name: Optional[str] = None,
        reason: Optional[str] = None,
        price: Optional[float] = None,
        eta: Optional[float] = None,
        rating: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        THE FEEDBACK LOOP.

        Capture an explicit human judgement about a decision the agent made,
        convert the judged item's attributes into normalised units, run one
        online weight update, persist the new weights, and append an auditable
        row recording the weight vector before and after.

        The next request for this user will be ranked with the updated weights.
        """
        profile = await self.get_profile(user_id)
        weights_before = dict(profile["weights"])

        attributes = normalise_attributes(price, eta, rating)
        weights_after = update_weights(weights_before, accepted, attributes)

        history: List[Dict[str, Any]] = list(profile.get("history") or [])
        history.append({
            "kind": "feedback",
            "accepted": accepted,
            "target_name": target_name,
            "reason": reason,
            "attributes": attributes,
            "at": datetime.utcnow().isoformat(),
        })
        history = history[-PROFILE_WINDOW:]

        await self._persist_profile(
            user_id=user_id,
            weights=weights_after,
            preferences=profile.get("preferences") or {},
            history=history,
            interaction_count=profile.get("interaction_count", 0) + 1,
            accept_count=profile.get("accept_count", 0) + (1 if accepted else 0),
            reject_count=profile.get("reject_count", 0) + (0 if accepted else 1),
        )

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO feedback_log
                (user_id, session_id, target_type, target_name, accepted, reason,
                 attributes_json, weights_before_json, weights_after_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    session_id,
                    target_type,
                    target_name,
                    1 if accepted else 0,
                    reason,
                    json.dumps(attributes),
                    json.dumps(weights_before),
                    json.dumps(weights_after),
                    datetime.utcnow().isoformat(),
                ),
            )
            await db.commit()

        return {
            "user_id": user_id,
            "accepted": accepted,
            "attributes": attributes,
            "weights_before": weights_before,
            "weights_after": weights_after,
            "delta": {
                k: round(weights_after[k] - weights_before[k], 4)
                for k in ("w1", "w2", "w3")
            },
        }

    async def reset_user(self, user_id: str) -> None:
        """Forget everything about a user (used to demonstrate cold start)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM user_memory WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM feedback_log WHERE user_id = ?", (user_id,))
            await db.commit()

    # -- internals ---------------------------------------------------------

    async def _persist_profile(
        self,
        user_id: str,
        weights: Dict[str, float],
        preferences: Dict[str, Any],
        history: List[Dict[str, Any]],
        interaction_count: int,
        accept_count: int,
        reject_count: int,
    ) -> None:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO user_memory
                (user_id, w1, w2, w3, interaction_count, accept_count, reject_count,
                 preferences_json, history_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    w1=excluded.w1, w2=excluded.w2, w3=excluded.w3,
                    interaction_count=excluded.interaction_count,
                    accept_count=excluded.accept_count,
                    reject_count=excluded.reject_count,
                    preferences_json=excluded.preferences_json,
                    history_json=excluded.history_json,
                    updated_at=excluded.updated_at
                """,
                (
                    user_id,
                    weights["w1"],
                    weights["w2"],
                    weights["w3"],
                    interaction_count,
                    accept_count,
                    reject_count,
                    json.dumps(preferences, ensure_ascii=False),
                    json.dumps(history, ensure_ascii=False),
                    now,
                    now,
                ),
            )
            await db.commit()


memory_store = UserMemoryStore()
