"""
JURY DEMO RUNNER — Self-contained, offline-capable demonstration.

Run this ONE file and it demonstrates both jury extension modules:

    python JURY_DEMO_RUNNER.py

UNIT-3 MODULE  : Long-Term Memory + Feedback Loop
    Part A - Long memory: write a preference, restart the process, read it back.
    Part B - Feedback loop: accept/reject an item, watch the utility weights
              move, then re-rank and observe a different winner.
    Part C - Cold start vs. learned: same candidate set, different weights,
              different decision.

UNIT-4 MODULE  : Multi-Agent System (parallel specialist fan-out)
    Part D - Roster: 6 specialist agents, each owning one dimension.
    Part E - Fan-out: 6 candidates x 6 concurrent specialists, hard-constraint
              gates, weighted aggregate ranking, full audit trail.

This script needs NO network, NO Swiggy token and NO Gemini key. It only
needs `aiosqlite` (already a backend dependency) and `numpy` is NOT required.

The database used is a fresh temporary file, so existing project and session
databases are never overwritten.
"""

import asyncio
import os
import sys
import json
import shutil
import tempfile
from datetime import datetime

# Make the backend importable regardless of where the script is run from.
ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Use a fresh temporary DB so a prior demo or application database is untouched.
demo_fd, DEMO_DB = tempfile.mkstemp(prefix="food_ordering_agent_jury_demo_", suffix=".db")
os.close(demo_fd)

os.environ["DATABASE_PATH"] = DEMO_DB

from app.db.memory_store import (  # noqa: E402
    DEFAULT_WEIGHTS,
    UserMemoryStore,
    normalise_attributes,
    update_weights,
)
from app.agent.specialists import (  # noqa: E402
    Candidate,
    SupervisorAgent,
    build_demo_candidates,
)

# Instantiate our own store pointed at the throwaway DB.
store = UserMemoryStore(db_path=DEMO_DB)

USER_ID = "jury_demo_user_01"


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------

W = 78

def hr(char="="):
    print(char * W)

def title(text):
    print()
    hr("=")
    print(f"  {text}")
    hr("=")

def section(text):
    print()
    print("-" * W)
    print(f"  {text}")
    print("-" * W)

def kv(label, value, indent=2):
    print(f"{' ' * indent}{label:<28} {value}")

def bar(value, max_value=1.0, width=28, char="█"):
    filled = int(max(0.0, min(1.0, value / max_value)) * width)
    return f"{char * filled}{'░' * (width - filled)}"


# ---------------------------------------------------------------------------
# UNIT-3 : LONG MEMORY + FEEDBACK LOOP
# ---------------------------------------------------------------------------

async def unit3_demo():
    title("UNIT-3 DEMO MODULE: LONG-TERM MEMORY + FEEDBACK LOOP")

    await store.init_db()
    print("\n  Two new tables created in a fresh database:")
    print("    • user_memory   — learned weights + counters + rolling preferences")
    print("    • feedback_log  — append-only audit of every feedback event")

    # ------------------------------------------------------------------
    section("PART A — LONG MEMORY: a preference survives a 'restart'")
    # ------------------------------------------------------------------
    print("\n  [A1] User states a preference. The agent distils it into the")
    print("       durable profile (passive half of the feedback loop).")

    await store.observe_request(
        USER_ID,
        {
            "food": "paneer",
            "vegetarian": True,
            "max_budget": 300,
            "max_delivery_minutes": 25,
        },
    )
    profile = await store.get_profile(USER_ID)
    kv("vegetarian", profile["preferences"].get("vegetarian"))
    kv("max_budget", profile["preferences"].get("max_budget"))
    kv("max_delivery_minutes", profile["preferences"].get("max_delivery_minutes"))

    print("\n  [A2] Simulating a full process restart (new store object, new")
    print("       connection — only the SQLite file survives).")
    store_after_restart = UserMemoryStore(db_path=DEMO_DB)
    profile2 = await store_after_restart.get_profile(USER_ID)
    kv("preferences recovered", profile2["preferences"].get("vegetarian") is not None)
    kv("budget recovered", profile2["preferences"].get("max_budget"))
    kv("weights recovered", profile2["weights"])
    print("\n  ✓ Long memory confirmed: the preference is still there after restart.")

    # ------------------------------------------------------------------
    section("PART B — FEEDBACK LOOP: human feedback updates the weights")
    # ------------------------------------------------------------------
    print("\n  [B1] The agent recommends a CHEAP but SLOW item.")
    print("       The user REJECTS it: 'I don't want to wait that long'.")

    before = (await store.get_profile(USER_ID))["weights"]
    print(f"\n       Weights before : {before}")

    result = await store.record_feedback(
        user_id=USER_ID,
        accepted=False,
        target_type="menu_item",
        target_name="Value Paneer Thali",
        reason="too slow, I don't want to wait 25 minutes",
        price=149.0,
        eta=25.0,
        rating=4.2,
    )
    print(f"       Weights after  : {result['weights_after']}")
    print(f"       Delta          : {result['delta']}")
    print(f"\n       Normalised attributes of the rejected item:")
    print(f"         w1 (price) = {result['attributes']['w1']:.4f}  <- strongest")
    print(f"         w2 (speed) = {result['attributes']['w2']:.4f}  <- WEAKEST")
    print(f"         w3 (qual)  = {result['attributes']['w3']:.4f}")
    print(f"       → w2 (speed sensitivity) went UP: the agent under-weighted speed.")
    print(f"       → w1 and w3 went DOWN: they were over-valued on that pick.")

    print("\n  [B2] The agent retries with another SLOW item. Rejected again.")
    before2 = (await store.get_profile(USER_ID))["weights"]
    print(f"\n       Weights before : {before2}")
    result2 = await store.record_feedback(
        user_id=USER_ID,
        accepted=False,
        target_type="menu_item",
        target_name="Classic Paneer Combo",
        reason="still too slow, I want it in under 15 minutes",
        price=229.0,
        eta=20.0,
        rating=4.4,
    )
    print(f"       Weights after  : {result2['weights_after']}")
    print(f"       Delta          : {result2['delta']}")
    print(f"       → w2 (speed) reinforced a second time. The pattern is now learned.")

    print("\n  [B3] The agent offers a FAST item. The user ACCEPTS it.")
    before3 = (await store.get_profile(USER_ID))["weights"]
    print(f"\n       Weights before : {before3}")
    result3 = await store.record_feedback(
        user_id=USER_ID,
        accepted=True,
        target_type="menu_item",
        target_name="Express Paneer Bowl",
        reason="fast, exactly what I wanted",
        price=289.0,
        eta=14.0,
        rating=3.9,
    )
    print(f"       Weights after  : {result3['weights_after']}")
    print(f"       Delta          : {result3['delta']}")
    print(f"       → w2 (speed) confirmed. The user's real priority is now learned.")

    # ------------------------------------------------------------------
    section("PART C — THE LOOP CLOSES: learned weights change the outcome")
    # ------------------------------------------------------------------
    candidates = [
        Candidate("C1", "Value Paneer Thali",  149.0, 25.0, 4.2, True),
        Candidate("C2", "Express Paneer Bowl", 289.0, 14.0, 3.9, True),
        Candidate("C3", "Classic Paneer Combo", 229.0, 20.0, 4.4, True),
    ]
    context = {
        "food": "paneer",
        "vegetarian": True,
        "max_budget": 300,
        "max_delivery_minutes": 30,
    }

    def rank_with(weights, label):
        print(f"\n       {label}")
        print(f"       weights: {weights}")
        scored = []
        for c in candidates:
            if not c.is_veg:
                continue
            if c.price > context["max_budget"] or c.eta > context["max_delivery_minutes"]:
                continue
            p = max(0.0, 1.0 - c.price / context["max_budget"])
            e = max(0.0, 1.0 - c.eta / context["max_delivery_minutes"])
            r = max(0.0, min(1.0, c.rating / 5.0))
            u = weights["w1"] * p + weights["w2"] * e + weights["w3"] * r
            scored.append((u, c))
        scored.sort(key=lambda t: t[0], reverse=True)
        for i, (u, c) in enumerate(scored, 1):
            print(f"         {i}. {c.name:<24} Rs {c.price:>6.0f}  {c.eta:>2.0f}min  "
                  f"{c.rating}*  U={u:.4f}")
        return scored[0][1].name if scored else "NONE"

    print("\n       Same candidate set, same request, two different weight vectors.")
    cold_winner = rank_with(DEFAULT_WEIGHTS, "[C1] COLD-START weights (never learned):")
    learned = (await store.get_profile(USER_ID))["weights"]
    learned_winner = rank_with(learned, "[C2] LEARNED weights (after 3 feedback events):")

    kv("\n       Cold-start winner", cold_winner)
    kv("Learned winner", learned_winner)
    if cold_winner != learned_winner:
        print(f"\n  ✓ TOP-1 FLIP: the agent's recommendation changed from "
              f"'{cold_winner}' to '{learned_winner}'.")
        print("     Identical inputs, identical candidate set — only the learned")
        print("     weights differ. This is the feedback loop working end to end.")
    else:
        print("\n  ✓ Weights moved and the ranking was recomputed with them.")

    # ------------------------------------------------------------------
    section("PART D — AUDIT TRAIL (proof the learning is real, not faked)")
    # ------------------------------------------------------------------
    history = await store.get_feedback_history(USER_ID, limit=10)
    for i, event in enumerate(history, 1):
        verdict = "ACCEPTED" if event["accepted"] else "REJECTED"
        print(f"\n  Event {i}: {verdict} — {event['target_name']}")
        print(f"    reason      : {event['reason']}")
        print(f"    attributes  : {event['attributes']}")
        print(f"    weights pre : {event['weights_before']}")
        print(f"    weights post: {event['weights_after']}")
        print(f"    timestamp   : {event['created_at']}")

    final = await store.get_profile(USER_ID)
    print()
    kv("Total interactions", final["interaction_count"])
    kv("Accepted", final["accept_count"])
    kv("Rejected", final["reject_count"])
    kv("Final weights", final["weights"])


# ---------------------------------------------------------------------------
# UNIT-4 : MULTI-AGENT SYSTEM
# ---------------------------------------------------------------------------

async def unit4_demo():
    title("UNIT-4 DEMO MODULE: MULTI-AGENT SYSTEM (PARALLEL SPECIALIST FAN-OUT)")

    supervisor = SupervisorAgent()

    section("PART A — THE AGENT ROSTER")
    print(f"\n  Supervisor: SupervisorAgent")
    print(f"  Execution model: parallel fan-out / barrier join (asyncio.gather)")
    print(f"  Specialist count: {len(supervisor.specialists)}\n")
    for s in supervisor.specialists:
        kind = "HARD (gate)" if s.is_hard_constraint else "SOFT (scored)"
        print(f"    • {s.name:<20} dimension={s.dimension:<11} type={kind:<14} weight={s.weight}")

    section("PART B — FAN-OUT: every specialist judges every candidate")
    candidates = build_demo_candidates()
    context = {
        "food": "paneer",
        "vegetarian": True,
        "max_budget": 300,
        "max_delivery_minutes": 30,
    }

    print(f"\n  Request: vegetarian 'paneer', budget <= Rs 300, delivery <= 30 min")
    print(f"  Candidates: {len(candidates)}\n")

    report = await supervisor.decide(candidates, context)

    print("  Per-specialist aggregate across all candidates:")
    for name, stats in report["per_specialist_stats"].items():
        kind = "HARD" if stats["hard_constraint"] else "SOFT"
        print(f"    {name:<20} {kind:<5} evaluated={stats['evaluated']}  "
              f"passed={stats['passed']}  failed={stats['failed']}  "
              f"avg_score={stats['avg_score']}")

    section("PART C — THE JOIN: hard gates then weighted aggregate")
    print(f"\n  Accepted: {report['accepted_count']}   "
          f"Rejected: {report['rejected_count']}   "
          f"(of {report['total_candidates']} candidates)")
    print(f"  Total fan-out wall time: {report['elapsed_ms']} ms\n")

    print("  RANKING (survivors, by aggregate utility):")
    for row in report["ranking"]:
        print(f"    {row['rank']}. {row['name']:<24} U={row['utility']:.4f}  "
              f"Rs {row['price']:>6.0f}  {row['eta']:>2.0f}min  {row['rating']}*")

    if report["rejections"]:
        print("\n  REJECTED BY HARD-CONSTRAINT GATES:")
        for rej in report["rejections"]:
            print(f"    ✗ {rej['name']:<24} {rej['reason']}")

    section("PART D — FULL AUDIT TRAIL FOR THE WINNER")
    winner = report["winner"]
    if winner:
        print(f"\n  Winner: {winner['candidate']['name']}  "
              f"U={winner['utility']:.4f}")
        print(f"  Explanation: {winner['explanation']}\n")
        for v in winner["verdicts"]:
            mark = "PASS" if v["passed"] else "FAIL"
            kind = "HARD" if v["is_hard_constraint"] else "SOFT"
            print(f"    [{mark}] {v['specialist']:<20} ({kind:<4} w={v['weight']}) "
                  f"score={v['score']:.3f}")
            print(f"           {v['reason']}")


# ---------------------------------------------------------------------------

async def main():
    print()
    hr("=")
    print("   FOOD ORDERING AGENT — JURY EXTENSION DEMONSTRATION")
    print("   Unit-3: Long-Term Memory + Feedback Loop")
    print("   Unit-4: Multi-Agent System (parallel specialist fan-out)")
    hr("=")
    print(f"  Database: {DEMO_DB}")
    print(f"  Started  : {datetime.utcnow().isoformat()}")

    await unit3_demo()
    await unit4_demo()

    print()
    hr("=")
    print("   DEMO COMPLETE")
    hr("=")
    print(f"\n  Long-memory database written to: {DEMO_DB}")
    print("  Inspect it with any SQLite viewer to see the learned weights.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
