# Food Ordering Agent: Project Architecture and Requirement Mapping

## Project overview

This project is a conversational food-ordering application. A Next.js frontend sends requests to a FastAPI backend. The backend uses a LangGraph `StateGraph` to orchestrate specialized food-ordering nodes, Gemini to interpret the initial request, and Swiggy MCP tools to retrieve food-service data and carry out supported ordering actions. SQLite persists session state between requests.

## High-level architecture

```text
User
  |
  v
Next.js frontend
  |  REST requests / session cookie
  |  Server-Sent Events for live agent state
  v
FastAPI backend
  +-- OAuth API -------- Swiggy OAuth + PKCE
  +-- Agent API -------- start / respond / confirm / state / addresses
  +-- Stream API ------- SSE updates from persisted session state
  |
  +-- LangGraph StateGraph (shared AgentState)
  |     understand -> plan -> restaurant search -> filter -> rank
  |       -> restaurant selection -> menu -> filter -> rank
  |       -> item selection -> customization -> cart
  |       -> payment -> human confirmation -> order -> tracking
  |                         |
  |                         +-- conditional wait / replan paths
  |
  +-- Gemini API -------- request understanding
  +-- Swiggy MCP -------- addresses, restaurant/menu/order tools
  +-- SQLite ------------ session, agent state, event log, encrypted token
```

## Main components

### Frontend

The Next.js application is under `frontend/src`. The main page coordinates login status, the user's food request, live agent state, and the ordering interface. Components present the timeline, requirements, restaurants and menus, cart, replanning prompt, payment selection, confirmation, and order tracking. API calls are centralized in `frontend/src/lib/api.ts`; live updates use the backend's Server-Sent Events (SSE) endpoint.

### Backend API and authentication

The FastAPI application is initialized in `backend/app/main.py`. It registers versioned authentication, agent, and stream routers.

- `backend/app/api/v1/auth.py` initiates Swiggy OAuth using PKCE, validates the callback state, and stores the resulting access token server-side.
- `backend/app/api/v1/agent.py` starts and resumes graph runs, fetches addresses and state, accepts user responses, and requires an explicit confirmation before order placement.
- `backend/app/api/v1/stream.py` streams changes in persisted agent state to the frontend.
- `backend/app/api/deps.py` provides the session identifier used by API requests.

### Orchestrated micro-agent-style workflow

`backend/app/agent/graph.py` constructs one LangGraph `StateGraph`. Its nodes are separated by responsibility and operate on the shared `AgentState` defined in `backend/app/agent/state.py`.

| Specialist node group | Responsibility |
|---|---|
| Understand | Extract food, cuisine, components, and constraints from the request using Gemini. |
| Plan | Prepare the requirements for the ordering workflow. |
| Restaurant | Search, parse, filter, rank, and select restaurants. |
| Menu | Retrieve, filter, rank, and select menu items. |
| Customization and cart | Apply item options and build the cart. |
| Payment and order | Present payment choices, wait for confirmation, and place the order. |
| Tracking | Retrieve or present order status. |
| Replan | Pause and ask the user whether constraints may be relaxed if results cannot satisfy them. |

The graph's conditional routes are defined in `backend/app/agent/routing.py`. Nodes report state changes through `backend/app/agent/nodes/utils.py`.

**Accurate terminology:** this is a **single orchestrated agent with specialized micro-agent-style nodes** (or a **modular, node-based multi-agent workflow**, if that is how the project requirement defines agents). The nodes are specialist units coordinated by a central graph and share state. They are not currently independent agent processes that negotiate, delegate dynamically, or each run their own reasoning loop. Request understanding is the node that calls Gemini; the rest of the workflow is primarily deterministic orchestration and integrations.

### External services

- **Gemini** is used by the understanding node to convert natural-language requests into structured requirements.
- **Swiggy MCP** is accessed through `backend/app/mcp/client.py`; OAuth and PKCE helpers are in `backend/app/mcp/oauth.py`, with response parsing in `backend/app/mcp/parsers.py`.

### Persistence and session memory

`backend/app/db/session_store.py` stores session records, agent state, progress flags, event-log JSON, and the encrypted Swiggy token in SQLite. The agent state is also used when a paused workflow resumes.

This provides **persistent per-session workflow memory**. It does not currently implement a durable user profile, cross-session preference recall, vector/semantic memory, or learning from past orders and ratings. A saved session is not the same as long-term personalized memory.

## Request lifecycle

1. The frontend checks authentication. The user connects a Swiggy account through the OAuth/PKCE flow.
2. The user submits a food request; the frontend calls `POST /api/v1/agent/start`.
3. The backend validates the session and address, initializes `AgentState`, persists it, and starts the LangGraph workflow in the background.
4. The understanding node calls Gemini to structure the request. Specialist nodes then search and rank restaurants and menu items through the workflow and available MCP tools.
5. The frontend receives state updates from `GET /api/v1/stream/{session_id}` and displays the corresponding step and results.
6. If the workflow needs a user decision, it pauses. `POST /api/v1/agent/respond` records payment selection or relaxed constraints and resumes the graph.
7. Before placing an order, the workflow waits for explicit user confirmation through `POST /api/v1/agent/confirm`. Following the order step, the graph may retrieve tracking information.

## Requirement mapping

| Requirement / capability | Current implementation | Assessment |
|---|---|---|
| Multi-agent or micro-agent architecture | Specialized nodes in a LangGraph graph share state and are centrally routed. | **Partially satisfies / depends on definition.** Strong evidence for modular specialist micro-agent-style nodes. Do not claim independent autonomous agents unless that requirement explicitly permits graph nodes to count as agents. |
| Planning and execution | A plan node and a sequence of specialist nodes execute the food-ordering workflow. | **Implemented as an orchestrated workflow.** |
| Memory | SQLite persists session state and event logs, and supports resuming the current session. | **Session-level persistence implemented.** Cross-session user-preference memory is not implemented. |
| Feedback loop | The replan path pauses for user input; relaxed constraints can be applied and the graph resumed. | **In-session corrective feedback implemented.** This is a user-directed replan loop, not a model-training or preference-learning loop. |
| Learning from ratings or outcomes | No persistent ratings/preferences feedback mechanism was found in the reviewed application code. | **Not currently implemented.** |
| Human oversight for ordering | The API and graph include a user confirmation checkpoint before order placement. | **Implemented.** |
| Live progress visibility | Backend SSE streams current state; frontend displays agent progress. | **Implemented.** |
| Persistent authentication/session data | SQLite stores session data; the Swiggy token is encrypted before persistence. | **Implemented for the current session/auth workflow.** |

## Suggested presentation wording

> The project implements a modular micro-agent-style food-ordering system using LangGraph. A central orchestrator coordinates specialist nodes for request understanding, planning, restaurant and menu selection, customization, payment, ordering, replanning, and tracking. The nodes share a typed workflow state and use conditional routes to pause for user input or continue execution. SQLite provides persistent session memory and resumable state. A user-in-the-loop feedback path allows constraints to be relaxed and the workflow rerun. The current implementation provides session memory and corrective in-session feedback; persistent cross-session preference learning is future work.

If asked whether this is a fully autonomous multi-agent system, clarify that the implementation is **node-based and centrally orchestrated**, rather than a set of independent agents communicating with one another.

## Scope notes

- This document describes the application structure and behavior reflected in the current source code; it does not assert availability of external Gemini or Swiggy services.
- Authentication credentials and API keys belong in local environment configuration and should not be included in project documentation.
- No application code was changed to produce this architecture document.
