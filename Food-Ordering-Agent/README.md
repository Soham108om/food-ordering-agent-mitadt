# AI Food Ordering Agent

An agentic food-ordering application that converts a natural-language request into an editable, human-approved order workflow. The system combines a Next.js frontend, FastAPI backend, LangGraph orchestration, Gemini intent extraction, and Swiggy MCP tools.

## What it does

- Parses a request such as “vegetarian pizza under ₹500 within 30 minutes” into structured constraints.
- Searches restaurants and menus, filters hard constraints, and ranks recommendations.
- Lets the user change the delivery address and edit or reject AI recommendations.
- Supports dietary/allergy notices, menu customization, cart totals, payment selection, and explicit confirmation before order placement.
- Streams workflow progress to the frontend and supports order tracking when the provider returns tracking data.
- Includes saved favorites/reorder tools, logout, persistent session state, and an optional image display when provider image URLs are available.
- Includes a six-specialist supervisor demo and a SQLite-based preference/feedback memory extension.

## Architecture

```text
Next.js / React UI
        │ REST + Server-Sent Events
        ▼
FastAPI API ── LangGraph ordering workflow ── Gemini
        │                    │
        │                    └── Swiggy MCP tools (search, cart, payment, order)
        └── SQLite session state and long-term preference memory
```

The ordering graph is a staged workflow. Separate from it, the Unit-4 supervisor evaluates candidate items with six specialist agents (dietary, budget, speed, relevance, quality, and value). Hard constraints act as gates; soft preferences contribute to ranking. The Unit-3 memory extension stores learned preference weights and an auditable feedback history in SQLite.

## Requirements

- Python 3.10 or later
- Node.js 18 or later and npm
- Gemini API key for natural-language request parsing
- Swiggy MCP/OAuth access for live restaurant, cart, payment, and order operations

There are no local model weights. Gemini is accessed through its hosted API. Live restaurant/menu data comes from the configured Swiggy MCP service; the experiment script also contains synthetic scenarios for offline analysis, not a production dataset.

## Local setup (Windows PowerShell)

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set your own `GEMINI_API_KEY`, Swiggy OAuth redirect URI, and a unique `SESSION_ENCRYPTION_KEY`. Generate a random encryption value with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Register `http://localhost:8000/api/v1/auth/callback` as the OAuth callback with the provider. Keep `.env` private; never commit API keys, OAuth tokens, or session databases.

### Start the backend

In the first terminal:

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API health response is at `http://localhost:8000/` and interactive API documentation is at `http://localhost:8000/docs`.

### Start the frontend

In a second terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The Next.js development server forwards `/api/v1` requests to the local backend.

## Jury/demo utilities

Run the offline extension demonstration from the project root:

```powershell
python JURY_DEMO_RUNNER.py
```

It demonstrates preference persistence, feedback-driven ranking weights, and the parallel specialist supervisor without a Gemini key or Swiggy login. It uses a fresh temporary SQLite database and does not overwrite the application session database.

For the browser extension demonstration, open `http://localhost:3000/extension` while both servers are running.

### Jury fallback if Swiggy OTP is unavailable

The ordering page needs a Swiggy-authenticated session for live provider calls. If sign-in is blocked by an OTP cooldown:

1. **Plan A:** If you can authenticate before the jury, keep the browser session active and do not log out. Avoid live order confirmation unless you intend to place a real order.
2. **Plan B:** Start the backend and frontend and open `http://localhost:3000/extension`. The Unit-3/Unit-4 extension page calls local memory/specialist APIs and does not require a Swiggy token. Demonstrate specialist verdicts and the accept/reject feedback loop.
3. **Plan C:** If the browser/backend demo is unavailable, run `python JURY_DEMO_RUNNER.py` from the project root. This is fully offline and demonstrates the same extension logic in the terminal.

Explain clearly that Plans B/C demonstrate the memory and specialist extensions, not live restaurant search or order placement. Use your recorded live-flow video/screenshots as evidence for the base ordering UI.

## Tests and checks

From the project root:

```powershell
python -m pytest backend\tests -q
Set-Location frontend
npm run build
```

The backend regression suite passed **48 tests** during jury-document preparation. A previous frontend production build passed; rerun it on the machine used for the jury before presenting.

## Data, privacy, and limitations

- The application does not include a locally trained model or a static restaurant dataset. Provider catalogues, prices, availability, and delivery estimates can change.
- Gemini and Swiggy MCP are external dependencies. Network errors and provider rate limits (including HTTP 429 responses) can interrupt live requests; avoid repeatedly retrying during an upstream outage.
- Food images may be absent from provider responses; the interface uses a fallback instead of claiming an image is available.
- Order IDs and tracking fields depend on the provider response. If an order result is ambiguous, verify it in the provider’s order history before attempting another order.
- An actual order is placed only after the user explicitly confirms it. Use a test account and do not confirm a real purchase during a demo unless intended.
- Local session and preference databases may contain personal data. Do not upload them with the submission.

## Jury submission materials

- [10-page technical report](JURY_REPORT_10_PAGE.docx) and [PDF copy](JURY_REPORT_10_PAGE.pdf)
- [Final presentation](JURY_PRESENTATION.pptx)
- [Architecture/demo reference](ARCHITECTURE_JURY_DEMO.md)
- [Offline demo runner](JURY_DEMO_RUNNER.py)
- [Quick reference card](JURY_QUICK_CARD.md)

Replace the remaining screenshot and demo-video placeholders with genuine captures from the running application. Add the fourth member’s name and actual contribution before final submission.

The older `PROJECT_TECHNICAL_REPORT.md`, `JURY_SLIDES.md`, and `JURY_QUICK_CARD.md` contain synthetic or scripted example metrics; do not present those as live production results.
