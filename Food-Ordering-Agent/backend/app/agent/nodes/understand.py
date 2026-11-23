import json
import re
import sys
import time
from google import genai
from app.core.config import settings
from app.agent.state import AgentState
from app.agent.prompts import UNDERSTANDING_PROMPT
from app.agent.nodes.utils import notify_state_update

# This module is also imported by standalone runners (JURY_DEMO_RUNNER, notebooks)
# that do not go through app.main, so guard stdout against cp1252 here too.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def understand_with_gemini(user_request: str) -> dict:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing. Please provide a valid key in environment or .env file.")

    client = genai.Client(api_key=api_key)

    max_retries = 3
    delay = 2.0

    # Transient Gemini failures that are worth retrying rather than aborting.
    retryable_markers = ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "403", "PERMISSION_DENIED")

    # Gemini's flash endpoints return 503 under load quite often, and a given
    # model may be throttled while a sibling is healthy. Walk the candidate
    # list so one busy model does not fail the whole request.
    models_to_try = [settings.GEMINI_MODEL] + [
        m for m in settings.gemini_fallback_models if m != settings.GEMINI_MODEL
    ]

    last_error: Exception | None = None

    for model in models_to_try:
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=(
                        UNDERSTANDING_PROMPT
                        + "\n\nUSER REQUEST:\n"
                        + user_request
                    )
                )
                text = response.text.strip()
                text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
                return json.loads(text)
            except Exception as e:
                last_error = e
                err_msg = str(e)
                if not any(marker in err_msg for marker in retryable_markers):
                    # Not a transient failure (e.g. malformed response) - surface it.
                    raise
                if attempt < max_retries:
                    print(f"Gemini transient failure on {model} ({type(e).__name__}). "
                          f"Retrying attempt {attempt}/{max_retries} in {delay}s...")
                    time.sleep(delay)
                    delay *= 1.5
                    continue
                # Model exhausted its retries - fall through to the next model.
                print(f"Model {model} exhausted retries; trying next candidate.")
                break

    raise last_error if last_error else RuntimeError("Gemini request failed with no model available.")

def understand_node(state: AgentState) -> AgentState:
    state["current_step"] = "UNDERSTAND"
    reqs = understand_with_gemini(state["user_request"])
    if state.get("vegetarian_preference"):
        reqs["vegetarian"] = True
    state["requirements"] = reqs
    
    if reqs.get("cuisine"):
        state["cuisine"] = reqs["cuisine"]
    if reqs.get("food_components"):
        state["food_components"] = reqs["food_components"]

    print("🧠 UNDERSTAND:", json.dumps(reqs, indent=2, ensure_ascii=False))
    notify_state_update(state)
    return state
