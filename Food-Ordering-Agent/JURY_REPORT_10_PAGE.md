# AI Food Ordering Agent
## Technical Project Report

**Agentic AI — End-Term Jury Examination**
**Submission date:** 24 November 2026
**Team:** Soham, Tanishka, Tushar, and one member to be added
**Report length:** 10 pages

### Project objective

Design and implement an AI-assisted food-ordering application that turns a user’s natural-language request into restaurant and menu recommendations, while preserving user control over delivery address, item choice, payment selection, and final order confirmation.

### Project at a glance

The application combines a Next.js web interface, a FastAPI service, a LangGraph workflow, Gemini-based request understanding, and Swiggy MCP tools for live provider operations. SQLite stores workflow/session state and a separate long-term preference/feedback profile. The order workflow pauses for user input at important decisions rather than placing an order autonomously.

**Keywords:** agentic AI, LangGraph, human-in-the-loop, recommendation, food ordering, MCP

---

# Page 2 — Problem Statement and Objectives

## Problem

Food-delivery users often need to compare multiple restaurants and menu items against several requirements at once: dish or cuisine, dietary preference, maximum price, delivery time, address, and payment method. A single ranking may not explain why an item was selected, and saved home addresses may not suit a user ordering from another location. Provider data can also change while an order is being prepared.

## Objective

Build an assistant that reduces the manual work of searching and comparing food options without removing the user’s authority over the purchase. The system should parse a request, find feasible choices, explain or display recommendations, allow edits, and require explicit approval before ordering.

## Project goals

1. Convert natural-language requests into structured food and delivery constraints.
2. Search live restaurants and menus through the configured provider tools.
3. Apply hard constraints before ranking feasible results.
4. Make recommendations editable and support alternate delivery addresses.
5. Keep users informed through streaming progress, payment selection, confirmation, and tracking.
6. Preserve session state and demonstrate a separate long-term preference/feedback mechanism.
7. Fail visibly when provider or model services are unavailable, rather than silently pretending an operation succeeded.

## Scope

The application is an integration prototype, not a food-delivery marketplace or a locally trained language model. Restaurant availability, fees, images, payment methods, order identifiers, and delivery estimates depend on external provider responses.

---

# Page 3 — Design Principles

## User control and safety

- **Human approval:** the workflow pauses for choices such as payment and requires explicit confirmation before order placement.
- **Editable recommendations:** users can change the selected restaurant or dish rather than accepting the AI’s first choice.
- **Address awareness:** a user can choose an available delivery address for the current order.
- **Clear failure handling:** provider errors, rate limits, and empty search results should be communicated as errors or replanning opportunities.

## Reliability and maintainability

- **Constraint-first ranking:** remove candidates that violate requested hard constraints before scoring preferences.
- **Modular responsibilities:** request understanding, planning, search, filtering, ranking, cart, payment, and tracking are separate workflow stages.
- **Persistent state:** save in-progress session data to SQLite so a paused workflow can be resumed.
- **Incremental extension:** the supervisor and memory demonstrations are added alongside the base ordering graph.

## Privacy and transparency

- Keep API keys, OAuth credentials, session tokens, and local databases out of source control and shared submissions.
- Encrypt stored provider tokens; use a unique `SESSION_ENCRYPTION_KEY` outside local demonstrations.
- Distinguish real provider data from synthetic experiment/demo candidates.
- Display a fallback when a provider does not supply a food image; do not invent an image or availability claim.

## Success criteria

The core success criterion is a user-visible flow from request through recommendation to an explicit confirmation gate. The optional Unit-3/Unit-4 extension criteria are persistent feedback weights, an auditable feedback history, and individual specialist verdicts in the candidate-ranking demo.

---

# Page 4 — System Block Diagram

## Component view

The browser UI communicates with the backend over REST endpoints and a Server-Sent Events stream. The backend coordinates the ordering graph, model-based request understanding, persistence, and provider tool calls.

**[Block diagram: browser UI → FastAPI → LangGraph workflow → Gemini / Swiggy MCP / SQLite]**

### Component responsibilities

| Component | Responsibility |
|---|---|
| Next.js / React frontend | Chat/request entry, address and recommendation choices, cart, payment, confirmation, and progress display |
| FastAPI API | Authentication/session endpoints, workflow start/respond/confirm, memory and specialist endpoints, and SSE |
| LangGraph | Stateful ordering stages and conditional routes for waiting, replanning, ordering, and tracking |
| Gemini API | Interprets natural-language food requests into structured requirements |
| Swiggy MCP | External restaurant/menu search, cart, payment, order, and tracking operations when available |
| SQLite | In-progress session data, encrypted provider token, user preference profile, and feedback audit |

### Data boundary

The frontend does not call the MCP provider directly. Provider operations and session handling are performed by the backend. The hosted Gemini model and Swiggy MCP service are external dependencies; local application code does not contain their model weights or provider catalogue.

---

# Page 5 — Technical Model Details

## Request understanding

The request-understanding stage sends the user’s text to the configured Gemini model and converts the response to structured fields such as food, cuisine, dietary preference, budget, and maximum delivery duration. A primary model and fallback model list are configurable through environment variables.

## Stateful workflow

The backend builds a LangGraph state graph. Its stages cover understanding, planning, restaurant search/filter/rank/selection, menu search/filter/rank/item selection, customization, cart, payment, order placement, and tracking. Conditional routing allows the graph to wait for the user, replan when there are no feasible options, or proceed after a confirmation.

## Candidate selection

Hard requirements (for example, vegetarian preference, budget ceiling, and delivery-time limit) are checked before candidates are recommended. Remaining candidates are ranked using available relevance, price, estimated time, and quality data. Values may be missing or change at the provider, so the interface must not treat a ranking score as a guarantee.

## Unit-4 specialist supervisor

An additional supervisor dispatches six specialist checks concurrently: dietary, budget, speed, relevance, quality, and value. Dietary, budget, and speed are hard gates; relevance, quality, and value contribute soft scores. The result includes verdicts and reasons that can be inspected in the offline demo.

## Unit-3 memory and feedback

SQLite stores per-user preferences and three utility weights for price, speed, and quality. Accept/reject feedback updates the weights using a bounded, normalized rule and records before/after values in an audit log. A new user starts with default weights. This is an application-level adaptive scoring mechanism, not a separately trained machine-learning model.

---

# Page 6 — Ordering Flowchart

## End-to-end flow

**[Flowchart: request → parse → address → search → filter/rank → user choice → menu/cart → payment → confirm → order → tracking]**

1. The user signs in and selects a delivery address.
2. The user describes the desired food and constraints.
3. The backend parses the request and searches restaurants.
4. The system filters candidates against hard constraints, then ranks feasible options.
5. The user accepts or changes the restaurant recommendation.
6. The system searches and ranks menu items; the user selects or edits the dish.
7. The cart is updated and the current price summary is shown.
8. The user chooses an available payment method.
9. The graph pauses until the user explicitly confirms the order.
10. The backend submits the order and displays provider status/tracking information when returned.

## Recovery paths

- If no restaurant or menu item meets the request, the workflow can ask the user whether to relax constraints or choose another query.
- If an external call fails, the UI should show the error; repeated retries may worsen an upstream rate limit.
- If an order response is ambiguous or has no order identifier, verify the provider’s order history before trying again.

---

# Page 7 — Working Model Screenshots (Steps 1–3)

> **Replace each marked box with an authentic screenshot from the running application. Keep personal addresses, account details, and tokens out of the capture.**

## Step 1 — Sign in and choose a delivery address

**[SCREENSHOT PLACEHOLDER 1: login/authenticated state and address selector]**

Caption to complete after capture: show the selected delivery address and explain that it can differ from the account’s home address.

## Step 2 — Enter a food request

**[SCREENSHOT PLACEHOLDER 2: request entry and parsed requirements]**

Caption to complete after capture: show a request with food, dietary preference, budget, and/or delivery-time constraints.

## Step 3 — Review restaurant recommendations

**[SCREENSHOT PLACEHOLDER 3: restaurant recommendation list and delivery estimates]**

Caption to complete after capture: show how the user can choose another restaurant instead of being forced to accept the first recommendation.

---

# Page 8 — Working Model Screenshots (Steps 4–6)

> **Replace each marked box with an authentic screenshot from the running application. Use a demo/test account and avoid exposing payment or personal data.**

## Step 4 — Select a menu item

**[SCREENSHOT PLACEHOLDER 4: menu, price, and dietary/image fallback details]**

Caption to complete after capture: show the selected item and any available customization or dietary information.

## Step 5 — Review cart and payment

**[SCREENSHOT PLACEHOLDER 5: cart summary and payment selection]**

Caption to complete after capture: show the cart total and the payment options actually returned by the provider.

## Step 6 — Confirm and view order status

**[SCREENSHOT PLACEHOLDER 6: explicit confirmation followed by returned order/tracking status]**

Caption to complete after capture: show the human confirmation gate and the order/tracking response. If the provider returns no order ID, state that accurately and verify the order in provider history.

---

# Page 9 — Data, Testing, and Evaluation

## Data and model

- **Hosted model:** Gemini, configured by `GEMINI_API_KEY`, `GEMINI_MODEL`, and `GEMINI_FALLBACK_MODELS`; no local model-weight file is included.
- **Live catalogue:** restaurant and menu data are fetched from the configured Swiggy MCP service and can vary by address and time.
- **Offline demo candidates:** the specialist supervisor and memory demo use deterministic sample candidates so their logic can be shown without provider access.
- **Experiment data:** `experimentation_suite.py` uses synthetic scenarios for analysis. Its plots are simulations, not measured production guarantees or a real-user dataset.

## Test results

| Check | Result |
|---|---|
| Backend regression tests | **48 passed** (`python -m pytest backend\tests -q`, 23 Nov 2026) |
| Frontend production build | Passed previously; rerun on the presentation machine before the jury |
| Offline Unit-3/Unit-4 demonstration | Completed successfully: six sample candidates, three accepted and three rejected with reasons; feedback changed the top-ranked item using the same candidate set |

Backend tests cover parsers, address handling, cart totals, dietary preferences, order tracking, no-match replanning, payment reuse, logout, streaming updates, and workflow request guards. A passing test suite does not guarantee external provider availability.

## Evidence to attach

**[SCREENSHOT PLACEHOLDER 7: terminal test results]**
**[VIDEO PLACEHOLDER: insert the recorded demo or add a Drive link]**

---

# Page 10 — Team Contributions and Conclusion

## Individual contributions

| Member | Reported contribution |
|---|---|
| Soham | Backend development; shared feature selection and workflow design |
| Tanishka | Backend development; shared feature selection and workflow design |
| Tushar | Frontend development; shared feature selection and workflow design |
| **Fourth member — add name** | **Add the member’s actual contribution before submission** |

Confirm these descriptions with every member before uploading. Do not list work that a member did not perform.

## Limitations

The live experience depends on external Gemini and Swiggy services, provider rate limits, and returned data. Restaurant availability, delivery estimates, payment methods, image URLs, and order IDs are not controlled by this application. The preference-learning extension has a cold-start state and should be treated as a small adaptive ranking demonstration, not a production recommender validated on a large user dataset.

## Conclusion

The project demonstrates an end-to-end agentic ordering workflow that combines natural-language understanding, constraint filtering, editable recommendations, stateful orchestration, external tools, persistent memory, and explicit human approval. Its main design choice is to let AI assist with search and comparison while leaving important purchase decisions with the user.

### References

1. Project source code and tests in `backend/` and `frontend/`.
2. Gemini API documentation: https://ai.google.dev/
3. LangGraph documentation: https://docs.langchain.com/oss/python/langgraph/overview
4. Model Context Protocol documentation: https://modelcontextprotocol.io/
