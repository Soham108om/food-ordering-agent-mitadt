"""
UNIT-4 DEMO MODULE: API surface for the Multi-Agent Supervisor System

Endpoints:
    GET  /api/v1/specialists/registry    -> the roster of specialist agents
    POST /api/v1/specialists/decide      -> run the supervisor over candidates
    GET  /api/v1/specialists/demo        -> run the built-in reproducible demo
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.specialists import (
    Candidate,
    SupervisorAgent,
    build_demo_candidates,
    run_unit4_demo,
    supervisor,
)

router = APIRouter(prefix="/specialists", tags=["Multi-Agent Supervisor System"])


class CandidateInput(BaseModel):
    item_id: str
    name: str
    price: float
    eta: float
    rating: float
    is_veg: bool
    is_bestseller: bool = False
    has_variants: bool = False


class DecideRequest(BaseModel):
    candidates: List[CandidateInput]
    context: Dict[str, Any] = {}


@router.get("/registry")
async def get_registry():
    """
    The agent roster. Each entry is a specialist that owns exactly one
    dimension of the decision, and each declares whether it is a hard
    constraint (pass/fail gate) or a soft preference (scored signal).
    """
    return {
        "supervisor": "SupervisorAgent",
        "execution_model": "parallel fan-out / barrier join (asyncio.gather)",
        "specialist_count": len(supervisor.specialists),
        "specialists": [
            {
                "name": s.name,
                "dimension": s.dimension,
                "constraint_type": "HARD" if s.is_hard_constraint else "SOFT",
                "join_weight": s.weight,
            }
            for s in supervisor.specialists
        ],
    }


@router.post("/decide")
async def decide(payload: DecideRequest):
    """
    Run the supervisor over a caller-supplied candidate set and context.

    Hard-constraint specialists act as gates: any candidate failing one is
    rejected outright. The survivors are ranked by the weighted aggregate of
    the soft-preference specialists.
    """
    candidates = [
        Candidate(
            item_id=c.item_id,
            name=c.name,
            price=c.price,
            eta=c.eta,
            rating=c.rating,
            is_veg=c.is_veg,
            is_bestseller=c.is_bestseller,
            has_variants=c.has_variants,
        )
        for c in payload.candidates
    ]
    return await supervisor.decide(candidates, payload.context or {})


@router.get("/demo")
async def demo():
    """
    The reproducible built-in demo used in the jury presentation.
    6 candidates x 6 concurrent specialists, with a full audit trail.
    """
    return await run_unit4_demo()
