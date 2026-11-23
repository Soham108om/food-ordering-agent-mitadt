"""
UNIT-4 DEMO MODULE: Multi-Agent System with Parallel Specialist Fan-Out

Core Concept Demonstrated:
  Multi-agent orchestration where a *supervisor* agent decomposes a task and
  dispatches specialised *specialist* agents that run CONCURRENTLY, each
  owning exactly one dimension of the decision. The supervisor then aggregates
  the specialist verdicts into a single decision.

Contrast with the existing sequential pipeline (`app/agent/graph.py`):
  * graph.py     - a single linear StateGraph, executed node-by-node.
  * specialists.py - a supervisor + N parallel specialists, joined at a barrier.

The unit of composition is the "agent" in both cases, but here the
parallelism and the join semantics are explicit, which is what makes this a
demonstrable Unit-4 artefact.

Specialists implemented:
    1. DietaryValidator  - hard constraint: is the item vegetarian?
    2. BudgetAuditor     - hard constraint: is the item within budget?
    3. SpeedAnalyst      - hard constraint: will it arrive in time?
    4. QualityCritic     - soft preference: rating + bestseller signal
    5. ValueAnalyst      - soft preference: cost efficiency vs quality

Each specialist returns a structured verdict, never mutates global state, and
is independently testable.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Verdict types
# ---------------------------------------------------------------------------

@dataclass
class Verdict:
    """A single specialist's structured judgement on one candidate."""
    specialist: str
    dimension: str
    passed: bool
    is_hard_constraint: bool
    score: float                       # 0.0 - 1.0, higher is better
    reason: str
    weight: float = 1.0                # contribution weight in the aggregate
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specialist": self.specialist,
            "dimension": self.dimension,
            "passed": self.passed,
            "is_hard_constraint": self.is_hard_constraint,
            "score": round(self.score, 4),
            "reason": self.reason,
            "weight": round(self.weight, 4),
            "metadata": self.metadata,
        }


@dataclass
class Candidate:
    """A normalised candidate item under evaluation by the specialists."""
    item_id: str
    name: str
    price: float
    eta: float
    rating: float
    is_veg: bool
    is_bestseller: bool = False
    has_variants: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "name": self.name,
            "price": self.price,
            "eta": self.eta,
            "rating": self.rating,
            "is_veg": self.is_veg,
            "is_bestseller": self.is_bestseller,
            "has_variants": self.has_variants,
        }


# ---------------------------------------------------------------------------
# Specialist agents
# ---------------------------------------------------------------------------

class SpecialistAgent:
    """Base class. A specialist is a pure function over a candidate."""

    name: str = "Specialist"
    dimension: str = "generic"
    is_hard_constraint: bool = False
    weight: float = 1.0

    async def evaluate(self, candidate: Candidate, context: Dict[str, Any]) -> Verdict:
        raise NotImplementedError

    # -- helpers used by concrete specialists ------------------------------

    @staticmethod
    def _budget(context: Dict[str, Any]) -> float:
        return float(context.get("max_budget") or 500.0)

    @staticmethod
    def _eta_limit(context: Dict[str, Any]) -> float:
        return float(context.get("max_delivery_minutes") or 30.0)


class DietaryValidator(SpecialistAgent):
    """Hard constraint specialist: dietary compliance."""

    name = "DietaryValidator"
    dimension = "dietary"
    is_hard_constraint = True
    weight = 3.0

    async def evaluate(self, candidate: Candidate, context: Dict[str, Any]) -> Verdict:
        wants_veg = bool(context.get("vegetarian", False))
        if not wants_veg:
            return Verdict(self.name, self.dimension, True, True, 1.0,
                           "No dietary constraint requested", self.weight)
        if candidate.is_veg:
            return Verdict(self.name, self.dimension, True, True, 1.0,
                           f"'{candidate.name}' is marked vegetarian", self.weight)
        return Verdict(self.name, self.dimension, False, True, 0.0,
                       f"'{candidate.name}' is non-vegetarian but vegetarian was required",
                       self.weight, {"required_veg": True})


class BudgetAuditor(SpecialistAgent):
    """Hard constraint specialist: monetary ceiling."""

    name = "BudgetAuditor"
    dimension = "budget"
    is_hard_constraint = True
    weight = 3.0

    async def evaluate(self, candidate: Candidate, context: Dict[str, Any]) -> Verdict:
        limit = self._budget(context)
        if candidate.price <= limit:
            headroom = (limit - candidate.price) / limit if limit else 0.0
            return Verdict(self.name, self.dimension, True, True, 1.0,
                           f"Rs {candidate.price:.0f} within Rs {limit:.0f}",
                           self.weight, {"headroom": round(headroom, 4)})
        over = candidate.price - limit
        return Verdict(self.name, self.dimension, False, True, 0.0,
                       f"Rs {candidate.price:.0f} exceeds Rs {limit:.0f} by Rs {over:.0f}",
                       self.weight, {"overshoot": round(over, 2)})


class SpeedAnalyst(SpecialistAgent):
    """Hard constraint specialist: delivery SLA."""

    name = "SpeedAnalyst"
    dimension = "speed"
    is_hard_constraint = True
    weight = 3.0

    async def evaluate(self, candidate: Candidate, context: Dict[str, Any]) -> Verdict:
        limit = self._eta_limit(context)
        if candidate.eta <= limit:
            slack = (limit - candidate.eta) / limit if limit else 0.0
            return Verdict(self.name, self.dimension, True, True, 1.0,
                           f"{candidate.eta:.0f} min within {limit:.0f} min SLA",
                           self.weight, {"slack_minutes": round(limit - candidate.eta, 2)})
        over = candidate.eta - limit
        return Verdict(self.name, self.dimension, False, True, 0.0,
                       f"{candidate.eta:.0f} min breaches the {limit:.0f} min SLA by {over:.0f} min",
                       self.weight, {"overshoot_minutes": round(over, 2)})


class QualityCritic(SpecialistAgent):
    """Soft preference specialist: rating and popularity."""

    name = "QualityCritic"
    dimension = "quality"
    is_hard_constraint = False
    weight = 1.5

    async def evaluate(self, candidate: Candidate, context: Dict[str, Any]) -> Verdict:
        rating_score = max(0.0, min(1.0, candidate.rating / 5.0))
        pop_bonus = 0.15 if candidate.is_bestseller else 0.0
        score = min(1.0, rating_score + pop_bonus)
        tags = []
        if candidate.is_bestseller:
            tags.append("bestseller")
        return Verdict(self.name, self.dimension, True, False, score,
                       f"{candidate.rating:.1f}* rating" + (" + bestseller bonus" if candidate.is_bestseller else ""),
                       self.weight, {"rating": candidate.rating, "bestseller": candidate.is_bestseller,
                                     "tags": tags})


class ValueAnalyst(SpecialistAgent):
    """Soft preference specialist: cost per unit of quality."""

    name = "ValueAnalyst"
    dimension = "value"
    is_hard_constraint = False
    weight = 1.0

    async def evaluate(self, candidate: Candidate, context: Dict[str, Any]) -> Verdict:
        budget = self._budget(context)
        price_score = max(0.0, 1.0 - (candidate.price / budget)) if budget else 0.0
        quality_score = max(0.0, min(1.0, candidate.rating / 5.0))
        score = (price_score * 0.6) + (quality_score * 0.4)
        return Verdict(self.name, self.dimension, True, False, score,
                       f"value score {score:.3f} (price {price_score:.2f}, quality {quality_score:.2f})",
                       self.weight, {"price_score": round(price_score, 4),
                                     "quality_score": round(quality_score, 4)})


class RelevanceScout(SpecialistAgent):
    """Soft preference specialist: does the item match what was asked for?"""

    name = "RelevanceScout"
    dimension = "relevance"
    is_hard_constraint = False
    weight = 1.2

    async def evaluate(self, candidate: Candidate, context: Dict[str, Any]) -> Verdict:
        requested = str(context.get("food") or "").strip().lower()
        name = candidate.name.lower()
        if not requested:
            return Verdict(self.name, self.dimension, True, False, 0.5,
                           "no specific dish requested", self.weight)
        if requested in name:
            return Verdict(self.name, self.dimension, True, False, 1.0,
                           f"exact match for '{requested}'", self.weight)
        tokens = [t for t in requested.split() if len(t) > 2]
        if tokens and any(t in name for t in tokens):
            return Verdict(self.name, self.dimension, True, False, 0.75,
                           f"partial match on '{requested}'", self.weight)
        return Verdict(self.name, self.dimension, True, False, 0.2,
                       f"'{candidate.name}' does not mention '{requested}'", self.weight)


# ---------------------------------------------------------------------------
# Supervisor agent
# ---------------------------------------------------------------------------

class SupervisorAgent:
    """
    The supervisor decomposes the decision, dispatches the specialist agents
    concurrently, joins their verdicts at a barrier, and produces a final
    ranked decision.

    Concurrency is real: every specialist's coroutine is scheduled with
    `asyncio.gather`, so the five specialists for one candidate run in
    parallel, and the candidates themselves are processed in parallel too.
    """

    def __init__(self, specialists: Optional[List[SpecialistAgent]] = None):
        self.specialists: List[SpecialistAgent] = specialists or [
            DietaryValidator(),
            BudgetAuditor(),
            SpeedAnalyst(),
            RelevanceScout(),
            QualityCritic(),
            ValueAnalyst(),
        ]

    async def evaluate_candidate(
        self,
        candidate: Candidate,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run all specialists on one candidate, concurrently."""
        started = time.perf_counter()
        verdict_list = await asyncio.gather(
            *(s.evaluate(candidate, context) for s in self.specialists)
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        verdicts = [v.to_dict() for v in verdict_list]
        hard_failures = [v for v in verdict_list if v.is_hard_constraint and not v.passed]

        if hard_failures:
            utility = 0.0
            decision = "REJECTED"
            explanation = hard_failures[0].reason
        else:
            weighted = sum(v.score * v.weight for v in verdict_list)
            total_weight = sum(v.weight for v in verdict_list)
            utility = weighted / total_weight if total_weight else 0.0
            decision = "ACCEPTED"
            passed_dims = [v.dimension for v in verdict_list if v.passed]
            explanation = (
                f"all hard constraints satisfied ({', '.join(passed_dims)}); "
                f"weighted utility {utility:.3f}"
            )

        return {
            "candidate": candidate.to_dict(),
            "verdicts": verdicts,
            "utility": round(utility, 4),
            "decision": decision,
            "explanation": explanation,
            "specialist_latency_ms": round(elapsed_ms, 3),
        }

    async def decide(
        self,
        candidates: List[Candidate],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Full supervisor pass: evaluate every candidate in parallel, filter out
        the ones that violate a hard constraint, rank the survivors by
        aggregate utility, and report the winner plus a full audit trail.
        """
        started = time.perf_counter()
        evaluations = await asyncio.gather(
            *(self.evaluate_candidate(c, context) for c in candidates)
        )
        total_ms = (time.perf_counter() - started) * 1000.0

        accepted = [e for e in evaluations if e["decision"] == "ACCEPTED"]
        rejected = [e for e in evaluations if e["decision"] == "REJECTED"]
        accepted.sort(key=lambda e: e["utility"], reverse=True)

        winner = accepted[0] if accepted else None

        # Per-specialist aggregate stats, to prove every agent actually ran.
        per_specialist: Dict[str, Dict[str, Any]] = {}
        for evaluation in evaluations:
            for verdict in evaluation["verdicts"]:
                entry = per_specialist.setdefault(
                    verdict["specialist"],
                    {
                        "dimension": verdict["dimension"],
                        "hard_constraint": verdict["is_hard_constraint"],
                        "weight": verdict["weight"],
                        "evaluated": 0,
                        "passed": 0,
                        "failed": 0,
                        "_score_sum": 0.0,
                    },
                )
                entry["evaluated"] += 1
                entry["passed" if verdict["passed"] else "failed"] += 1
                entry["_score_sum"] += verdict["score"]
        for entry in per_specialist.values():
            entry["avg_score"] = round(entry.pop("_score_sum") / max(1, entry["evaluated"]), 4)

        return {
            "supervisor": "SupervisorAgent",
            "specialist_count": len(self.specialists),
            "specialists": [s.name for s in self.specialists],
            "context": context,
            "total_candidates": len(candidates),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "ranking": [
                {
                    "rank": i + 1,
                    "item_id": e["candidate"]["item_id"],
                    "name": e["candidate"]["name"],
                    "utility": e["utility"],
                    "price": e["candidate"]["price"],
                    "eta": e["candidate"]["eta"],
                    "rating": e["candidate"]["rating"],
                }
                for i, e in enumerate(accepted)
            ],
            "rejections": [
                {
                    "item_id": e["candidate"]["item_id"],
                    "name": e["candidate"]["name"],
                    "reason": e["explanation"],
                }
                for e in rejected
            ],
            "per_specialist_stats": per_specialist,
            "winner": winner,
            "elapsed_ms": round(total_ms, 3),
        }


#: Module-level supervisor used by the API layer.
supervisor = SupervisorAgent()


# ---------------------------------------------------------------------------
# Demo scenario
# ---------------------------------------------------------------------------

def build_demo_candidates() -> List[Candidate]:
    """A fixed candidate set so the demo output is reproducible."""
    return [
        Candidate("C1", "Paneer Butter Masala", 289.0, 24.0, 4.4, True, is_bestseller=True),
        Candidate("C2", "Margherita Pizza",   199.0, 31.0, 4.6, True),
        Candidate("C3", "Chicken Biryani",    349.0, 22.0, 4.7, False, is_bestseller=True),
        Candidate("C4", "Veg Pulao Bowl",      179.0, 18.0, 3.9, True),
        Candidate("C5", "Butter Chicken 5",   419.0, 27.0, 4.2, False),
        Candidate("C6", "Dal Tadka Combo",    229.0, 26.0, 4.1, True, has_variants=True),
    ]


async def run_unit4_demo() -> Dict[str, Any]:
    """
    Run the Unit-4 multi-agent demo end to end and return a report that is
    both human-readable and machine-consumable.
    """
    context = {
        "food": "paneer",
        "vegetarian": True,
        "max_budget": 300,
        "max_delivery_minutes": 30,
    }
    candidates = build_demo_candidates()
    report = await supervisor.decide(candidates, context)

    report["context_description"] = (
        "Request: vegetarian paneer, budget <= Rs 300, delivery <= 30 min. "
        f"{len(candidates)} candidates evaluated by {len(supervisor.specialists)} "
        "concurrent specialist agents."
    )
    return report
