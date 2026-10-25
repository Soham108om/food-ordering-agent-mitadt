import json
import re
import time
from google import genai
from app.core.config import settings
from app.agent.state import AgentState
from app.agent.prompts import UNDERSTANDING_PROMPT
from app.agent.nodes.utils import notify_state_update

def understand_with_gemini(user_request: str) -> dict:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing. Please provide a valid key in environment or .env file.")

    client = genai.Client(api_key=api_key)
    
    max_retries = 3
    delay = 2.0

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
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
            err_msg = str(e)
            if ("503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg) and attempt < max_retries:
                print(f"⚠️ Gemini API experiencing high demand (503). Retrying attempt {attempt}/{max_retries} in {delay}s...")
                time.sleep(delay)
                delay *= 1.5
            else:
                raise e

def understand_node(state: AgentState) -> AgentState:
    state["current_step"] = "UNDERSTAND"
    reqs = understand_with_gemini(state["user_request"])
    state["requirements"] = reqs
    
    if reqs.get("cuisine"):
        state["cuisine"] = reqs["cuisine"]
    if reqs.get("food_components"):
        state["food_components"] = reqs["food_components"]

    print("🧠 UNDERSTAND:", json.dumps(reqs, indent=2, ensure_ascii=False))
    notify_state_update(state)
    return state
