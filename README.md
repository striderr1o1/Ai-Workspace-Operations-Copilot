# AI Workspace Operations Copilot

> **🚧 Work in progress.** I'm actively building this — it is not finished software and not
> production-ready. Interfaces move between commits, some pieces documented in
> `self_docs/` are intent rather than shipped code, and a few known gaps are listed under
> [Project status](#project-status) below. Read this README as a snapshot of where the
> project is today, not as a stable contract.

A multi-agent orchestration system built on **LangGraph** that turns natural language into
workspace actions. An orchestrator agent interprets each request and routes it to
specialized sub-agents — a **Knowledge Base Agent** for document Q&A (RAG) and a **Booking
Agent** for reservation slots — then composes a single, coherent answer for the user.

The backend is a **FastAPI** service exposing synchronous and streaming query endpoints,
a document-ingestion endpoint, Supabase-backed auth, and an evaluation layer. The product
front end is **Receptix**, a React SPA in a separate repo that packages all of this as an
"AI front desk" a business can publish for its own customers. A **Streamlit** client is
also kept around for quick local pokes at the API.

## Architecture

```
              POST /query  ·  POST /query-agent (SSE)      ← Authorization: Bearer <jwt>
                                  |
                                  v
                          +----------------+
                          |  Orchestrator  |   OpenRouter — GPT-OSS-120B
                          |  (LangGraph)   |   (structured output via instructor)
                          +----------------+
                             /          \
                            v            v
               +----------------+   +----------------+
               |   KB Agent     |   | Booking Agent  |
               | (Groq/GPT-OSS) |   | (Groq/GPT-OSS) |
               +----------------+   +----------------+
                       |                    |
                       v                    v
              +----------------+    +----------------+
              |    Pinecone    |    |    Supabase    |
              |  (Vector DB)   |    |  (PostgreSQL)  |
              +----------------+    +----------------+
```

The orchestrator and sub-agents share a single LangGraph state machine. Structurally it is
**one loop, not a pipeline**: all three nodes route through the same conditional function
(`tool_call_node`), each with identical edges to `{end, knowledge_base_agent,
booking_agent, orchestrator}`, so a sub-agent can hand straight to another sub-agent
without a return trip through the orchestrator.

Termination has two independent brakes: the orchestrator's own `return_to_user` flag, and a
hop counter in `agent.py` that forces the decision true once `count > 3` regardless of what
the LLM asked for. Sub-agent nodes consume `tool_calls` destructively — each copies the
list, removes the entry it served, and returns the remainder — so the queue drains as the
graph runs.

**Query flow**
1. An authenticated user submits a natural-language query to `/query` (synchronous) or
   `/query-agent` (streaming SSE).
2. `check_session_exists` verifies the bearer token against Supabase and hands the route the
   caller's `id` and `access_token`.
3. The orchestrator analyzes intent and emits structured tool calls naming the sub-agent(s)
   to invoke.
4. Each sub-agent runs its own tools — Pinecone vector search for the KB Agent, Supabase
   CRUD for the Booking Agent — and returns a result.
5. Control returns to the orchestrator, which either dispatches another step or finalizes a
   summary for the user.

**Ingestion flow**
1. A PDF is uploaded to `/ingestion` together with a target namespace.
2. The document is split into chunks (1000 chars, 200-char overlap).
3. Chunks are embedded with OpenRouter (`nvidia/llama-nemotron-embed-vl`), truncated to 1024
   dimensions (Matryoshka), and batched.
4. Vectors are upserted into Pinecone under the given namespace.

### Per-request identity

Nothing about the caller travels through the prompt. The auth dependency returns
`{id, email, ..., access_token}`; `dependencies.py` passes both the user id and the JWT into
the agent factories, which attach them with LangChain's `RunnableConfig`
(`agent.with_config({"configurable": {...}})`). LangGraph threads that config down to the
tools, so each `@tool` reads `config["configurable"]["user_id"]` directly — the LLM can
neither see nor forge it.

The booking tools then build a **per-call** Supabase client with the caller's JWT
(`get_supabase_client_with_token`) so `auth.uid()` resolves inside RLS policies, and scope
every query with `.eq("business_id", user_id)` on top.

### Two kinds of Supabase client, deliberately

`services/supabase_client.py` exposes three accessors and they are not interchangeable:

| Accessor | Lifetime | Used by |
|---|---|---|
| `get_supabase_client()` | shared module-level | general/project-key access |
| `get_supabase_client_with_token(token)` | per request | booking tools, as the calling user |
| `create_auth_client()` | per call, thrown away | `auth_logic.py` |

supabase-py stores the signed-in session **on the client instance**. Calling
`sign_in_with_password` on the shared client would leave every later request in the
process — booking tools included — carrying that user's JWT instead of the project key,
which is a cross-request identity leak in a running server. `persist_session=False` does not
prevent this; the session still lands in memory. Hence the separate clients, with
`auto_refresh_token=False` so discarded clients don't leave refresh timer threads behind.

### Structured output is provider-sensitive

The orchestrator uses `instructor` in `Mode.JSON_SCHEMA` over OpenRouter, and
`get_chat_completion` passes `extra_body={"provider": {"require_parameters": True}}`. That
flag makes OpenRouter route only to providers that actually honour the strict
`response_format`; without it, requests can land on a provider that ignores it and returns
unconstrained prose, which fails parsing intermittently rather than loudly.

Model names are hardcoded in **two** places, not configured: the orchestrator model string
is an argument in `agents/agent.py` (`openai/gpt-oss-120b`), and the sub-agent model is in
`agents/agent_config.py` (`ChatGroq(model="openai/gpt-oss-20b")`).

## Tech Stack

| Component         | Technology                                                        |
|-------------------|-------------------------------------------------------------------|
| Orchestration     | LangGraph (state machine + conditional routing, retry policies)   |
| Orchestrator LLM  | OpenRouter — `openai/gpt-oss-120b`, structured output via `instructor` |
| Sub-agent LLM     | Groq — `openai/gpt-oss-20b`, `temperature=0`                      |
| Embeddings        | OpenRouter — `nvidia/llama-nemotron-embed-vl` (1024-dim, Matryoshka-truncated) |
| Vector Store      | Pinecone (serverless, cosine, namespaced)                         |
| Database & Auth   | Supabase (PostgreSQL + GoTrue)                                     |
| Web Framework     | FastAPI                                                           |
| Product frontend  | React 19 + Vite SPA (separate repo, GitHub Pages)                 |
| Dev/demo UI       | Streamlit                                                         |
| Observability     | LangSmith (optional)                                              |
| Deployment        | Docker (Railway-ready, binds `$PORT`)                            |

> **Note on embeddings:** ingestion and retrieval must use the *same* embedding model so
> query and document vectors share a space. The codebase currently uses OpenRouter; Google
> Gemini (`gemini-embedding-001`) and local Ollama (`mxbai-embed-large`) implementations are
> also present in `embedding_config.py` and can be swapped in. All three are configured to
> output 1024-dim vectors to match the Pinecone index.

## Project Structure

```
backend/
├── src/
│   ├── agents/
│   │   ├── agent.py            # Orchestrator + sub-agent node logic, hop counter
│   │   ├── agent_config.py     # LLM clients, agent factories, system prompt
│   │   ├── graph.py            # LangGraph state machine wiring + checkpointer
│   │   └── state.py            # TypedDict graph state + Pydantic schemas
│   ├── KnowledgeBaseTool/
│   │   ├── ingestion.py        # PDF load → chunk → embed → Pinecone upsert
│   │   ├── retrieval.py        # Query embed + Pinecone similarity search
│   │   ├── embedding_config.py # OpenRouter / Google / Ollama embedding fns
│   │   └── kb_tools.py         # LangChain tool wrappers (ingest, retrieve, namespaces)
│   ├── routes/
│   │   ├── inference.py        # /query and /query-agent (streaming) — auth required
│   │   ├── ingestion.py        # /ingestion (PDF upload)
│   │   ├── eval.py             # /eval/* evaluation endpoints — auth required
│   │   └── auth.py             # /auth/signup and /auth/login
│   ├── services/
│   │   ├── supabase_client.py  # Shared / per-request / per-auth-call clients
│   │   ├── booking_tools.py    # Slot tools (fetch/insert/update), scoped by business_id
│   │   └── auth_logic.py       # Supabase Auth signup/login + session dependency
│   ├── utils/
│   │   ├── exceptions.py       # Ingestion / Retrieval / Authentication errors
│   │   └── exception_handlers.py  # App-level handler for errors raised in dependencies
│   ├── dependencies.py         # Per-request graph assembly + inference runners
│   └── main.py                 # FastAPI app, CORS allowlist, router registration
├── evals/
│   ├── evaluation_engine.py        # Scenario loader + graders
│   └── orchestrator_dataset.json   # 60 hand-written orchestrator scenarios
├── ui/
│   └── streamlit_ui.py         # Streamlit dev client
├── self_docs/                  # Dated working notes / task list
├── tests/                      # Manual tool-level scripts (not tracked in git)
├── Dockerfile
├── requirements.txt
└── .env
```

### Import layout

Modules import each other as `from agents...`, `from services...`, `from routes...` — **not**
`src.agents...`. `src/` must be on the path, so either run from inside `src/` or set
`PYTHONPATH=src`. The `PYTHONPATH=src` line in `.env` is read by `python-dotenv` at runtime
and does *not* affect module resolution for the interpreter that is already starting up.
`evals/evaluation_engine.py` bootstraps this itself (inserts `src/` on `sys.path`, loads
`.env` from the repo root) because it lives outside `src/`, and `routes/eval.py` in turn
inserts the repo root to reach `evals/`.

## Authentication

Signup and login are Supabase Auth (GoTrue). Raw passwords are forwarded to Supabase and
nowhere else — this layer never persists, logs, or returns one.

Errors travel as `AuthenticationError` (`utils/exceptions.py`), which carries the status
code Supabase reported. `routes/auth.py` re-raises it as an `HTTPException`; the
app-level handler in `main.py` covers the dependency path, because a `Depends(...)` runs
*before* the route body and so is never caught by a route's own `try/except`. GoTrue answers
400 for bad credentials, which `sign_in` rewrites to 401.

### `POST /auth/signup`

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "owner@example.com", "password": "hunter2!"}'
```

Returns `{ user, session, requires_email_confirmation }`. With email confirmation enabled
(the current project setting) `session` is `null` and `requires_email_confirmation` is
`true` — the user is registered but not logged in until they click the emailed link.

### `POST /auth/login`

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "owner@example.com", "password": "hunter2!"}'
```

Returns `{ user, session }`, where `session.access_token` is the JWT to send back as
`Authorization: Bearer <token>` on every protected endpoint.

### Protected endpoints

`check_session_exists` asks GoTrue to validate the token rather than decoding it locally, so
a revoked session or deleted user is rejected immediately instead of staying trusted until
the token's own expiry.

| Endpoint | Auth |
|---|---|
| `POST /auth/signup`, `POST /auth/login` | public |
| `POST /query`, `POST /query-agent` | **bearer token required** |
| `GET /eval/dataset`, `POST /eval/{category}` | **bearer token required** |
| `POST /ingestion` | public — see [Project status](#project-status) |

## API Endpoints

### `POST /query`

Run a query synchronously and return the final graph state.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "What slots are available today?"}'
```

### `POST /query-agent`

Same input as `/query`, but streams progress as **Server-Sent Events** — emitting
`agent calls`, `knowledge base agent`, `booking agent`, and `final response` events as the
graph executes. This is what both frontends use for live status.

```bash
curl -N -X POST http://localhost:8000/query-agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "Book Sarah in from 2pm to 3pm today"}'
```

### `POST /ingestion`

Upload a PDF to be chunked, embedded, and stored in the knowledge base.

**Form fields**
- `file` — the PDF file
- `namespace_name` — Pinecone namespace to store the document under

```bash
curl -X POST http://localhost:8000/ingestion \
  -F "file=@document.pdf" \
  -F "namespace_name=workspace-docs"
```

### `GET /eval/dataset`

Return `orchestrator_dataset.json` along with a per-category index (`category`, `endpoint`,
`count`). Read-only and cheap — it runs no evaluation. The frontend uses it to populate the
scenario dropdown and preview the cases before running them.

### `POST /eval/{category}`

Run the orchestrator evaluation for one scenario category — see [Evaluation](#evaluation).
One endpoint per category: `initial-routing`, `after-booking-response`, `after-kb-response`,
`empty-agent-response`, `irrelevant`.

```bash
curl -X POST http://localhost:8000/eval/initial-routing -H "Authorization: Bearer $TOKEN"
```

All five return the same report shape, so a caller can render any category without knowing
which assertion that category's grader made:

```json
{
  "category": "initial_routing",
  "total": 20, "passed": 17, "failed": 3,
  "cases": [
    { "id": 1, "correct": true, "query": "What rooms are available right now?",
      "expected": { "decisions": [ { "tool_calls": ["booking_agent"], "return_to_user_decision": false } ] },
      "actual": { "tool_calls": [ { "tool": "booking_agent", "argument": ["..."] } ],
                  "return_to_user_decision": false, "response_to_user": "", "count": 1 } }
  ]
}
```

`actual` is the orchestrator's raw state delta, unmodified. The orchestrator swallows its
own exceptions into a dict containing only `return_to_user_decision: True` and an error
string — with no `tool_calls` key at all — which the graders score as a failure rather than
mistaking it for a correct "give up gracefully" decision. The report passes it straight
through instead of hiding it. Each call issues one LLM request per scenario, so a
20-scenario category takes a couple of minutes.

## Frontend

The product front end lives in a separate repo,
[`operations-copilot-js`](https://github.com/striderr1o1/operations-copilot-js) — a **React
19 + Vite** SPA branded **Receptix**, deployed to GitHub Pages by a workflow on every push
to `main`. It replaces the earlier no-build static pages.

The premise it is built around: a business signs up, feeds the copilot its documents, then
publishes a front desk on a shareable URL. Their customers use that URL with no account of
their own.

| Route | What it is |
|---|---|
| `/` | Marketing home — hero with a particle canvas, how-it-works, pricing, about, contact |
| `/get-started`, `/login` | Signup/login against `/auth/*`, one page with a mode toggle |
| `/dashboard/chatbot` | Operator chat against `/query-agent`, with per-agent reasoning blocks and an activity log; publish/unpublish switch and the shareable link |
| `/dashboard/ingestion` | Drag-and-drop PDF upload to `/ingestion`, PDF-only, 25 MB cap, remembers the namespace |
| `/dashboard/evaluations` | Category picker → scenario preview → run → pass/fail table |
| `/c/:slug` | The published, customer-facing chat — same stream, reasoning blocks hidden |

Notes on how it talks to this backend:

- The session (`{user, session}`) is stored in `localStorage` under `receptix.session`;
  `api.js` attaches `Authorization: Bearer …` to every call and clears the session on any
  401, which drops the UI back to login rather than leaving a dashboard 401-ing underneath.
- `src/lib/api.js` resolves the API base from `?api=…`, then `VITE_API_BASE`, then
  `http://localhost:8000`. Appending `?api=http://127.0.0.1:8000` to any page points it at a
  local server.
- `npm run dev` serves on **port 5173**, which is on the CORS allowlist hardcoded in
  `src/main.py` (alongside 3000, Streamlit's 8501, `null`, and the Pages origin). New
  origins have to be added there by hand.
- Publish state is currently **client-side only** (`localStorage`, `receptix.deployment`) —
  the backend has no deployment endpoints yet, so the live/unlive switch and slug are held
  in the browser. `src/lib/deployment.jsx` is the single file that changes when the API grows
  a deployments route.

`tests/e2e.mjs` drives the running dev server rather than starting one, and points Playwright
at a system Chromium — start `npm run dev` first, and expect to adjust `executablePath` on a
machine that isn't mine.

```bash
# in the frontend repo
npm install
npm run dev          # http://localhost:5173
npm run test:e2e     # Playwright pass over desktop + mobile viewports
```

## Evaluation

**There is no runnable pytest suite** — `tests/` is gitignored and holds manual scripts
driven by commented-out calls at the bottom of each file. The eval layer is the regression
suite.

Routing is the part of this system most likely to regress silently: a prompt tweak that
improves one kind of request can quietly break another, and nothing crashes when it does.
`evals/` exists to catch that.

**What is measured.** `orchestrator_dataset.json` holds 60 hand-written scenarios that each
pin down the exact graph state the orchestrator node sees, then check the single decision it
makes from that state. Sub-agents are never invoked — the engine calls
`agentic_workflow.orchestrator(state)` directly, since that method reads only `messages`,
`booking_agent_output`, `knowledge_base_agent_output`, and `count`. One LLM call per
scenario, no database or vector-store access, and the code under test is the production node
rather than a copy of it.

**Categories**

| Category                 | N  | Question it answers                                                |
|--------------------------|----|--------------------------------------------------------------------|
| `initial_routing`        | 20 | Straight after START, does it pick the right sub-agent?            |
| `after_booking_response` | 10 | Booking output is present — return to the user, or keep going?     |
| `after_kb_response`      | 10 | Knowledge base output is present — same question                   |
| `empty_agent_response`   | 10 | An agent was called and returned nothing. Retry, or fail honestly? |
| `irrelevant`             | 10 | Greetings and out-of-scope asks that no sub-agent should handle    |

**How scenarios are graded.** `expected.decisions` is a *list* of acceptable decisions, not a
single golden answer — routing isn't deterministic and several scenarios have more than one
defensible next step. Scenario 17 ("Is room 2 free at 3pm? Also, what's the meeting room
usage policy?") accepts queueing both agents or starting with either one, because all three
lead to a correct final answer. A scenario passes if the produced decision matches any entry.

Each category asserts something different — `initial_routing` compares tool calls only, the
`after_*` pair allows either returning or queueing more, `empty_agent_response` checks the
tool calls *and* the return decision together, and `irrelevant` additionally requires a
non-empty `response_to_user` — but `build_report` folds all five into one report shape so the
frontend renders them identically.

Each decision is keyed to mirror the orchestrator's own state delta:

```json
{
  "id": 1, "category": "initial_routing",
  "state": { "messages": [ { "role": "user", "content": "What rooms are available right now?" } ],
             "booking_agent_output": "", "knowledge_base_agent_output": "", "count": 0 },
  "expected": { "decisions": [ { "tool_calls": ["booking_agent"], "return_to_user_decision": false } ] },
  "reference_response": ""
}
```

`tool_calls` lists just the agent names; the free-form `argument` the orchestrator sends each
agent is not graded. Agent names are compared as a set, so ordering within a single decision
doesn't matter. `reference_response`, where non-empty, is a known-good reply kept for judging
response relevancy.

**Failure modes deliberately covered.** Beyond happy-path routing, the dataset targets the
ways an agent is dishonest rather than broken:

- Relaying a booking conflict instead of claiming success (28)
- Saying "not found" instead of inventing a policy (37)
- Not claiming a booking or cancellation succeeded when no confirmation came back (42, 44)
- Stopping once the retry budget is spent rather than looping (49, 50)

## Getting Started

### Prerequisites

- Python 3.11
- Pinecone account (serverless index, 1024-dim, cosine)
- Supabase project
- API keys: OpenRouter (orchestrator + embeddings) and Groq (sub-agents)

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file:
   ```env
   # LLMs
   GROQ_API_KEY=
   OPENROUTER_API_KEY=

   # Vector store
   PINECONE_API_KEY=
   PINECONE_INDEX_NAME=
   INDEX_URL_PINECONE=

   # Database + auth
   SUPABASE_URL=
   SUPABASE_KEY=               # currently the service_role key — see the caveat below

   # Embedding alternatives (optional)
   GOOGLE_API_KEY=             # for Gemini embeddings
   EMBEDDING_MODEL=mxbai-embed-large:latest   # for local Ollama embeddings

   PYTHONPATH=src

   # Optional — LangSmith observability
   LANGSMITH_TRACING=true
   LANGSMITH_ENDPOINT=
   LANGSMITH_API_KEY=
   LANGSMITH_PROJECT=
   ```

3. Create the Supabase `slots` table, which the booking tools read and write:

   | Column            | Type          | Notes                                        |
   |-------------------|---------------|----------------------------------------------|
   | `slotid`          | uuid          | primary key                                  |
   | `business_id`     | uuid          | the owning user's auth id — every query is scoped by it |
   | `time_start`      | timestamptz   | reservation start                            |
   | `time_end`        | timestamptz   | reservation end                              |
   | `occupier_email`  | citext        | who the slot is booked for                   |

   No schema is tracked in this repo (`supabase/` is gitignored), so all DDL lives in the
   Supabase dashboard. The columns above are what `services/booking_tools.py` assumes.

### Run the API

```bash
cd src
uvicorn main:app --reload
```

The API is served at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`. Anything invoked from the repo root instead needs the path set
explicitly: `PYTHONPATH=src python -c "from main import app"`.

### Run the Streamlit client

```bash
streamlit run ui/streamlit_ui.py      # expects the API on localhost:8000
```

### Run with Docker

```bash
docker build -t ops-copilot . && docker run -p 8000:3000 --env-file .env ops-copilot
```

The container runs uvicorn from `src/` and binds to `$PORT` (defaults to `3000`), making it
deployable to Railway and similar platforms.

## Project status

What works end to end today: signup/login, an authenticated streaming chat that routes
between the two sub-agents, PDF ingestion into namespaced Pinecone corpora, per-user scoping
of booking data, and the five-category evaluation suite with a UI to run it.

Known gaps I'm still working on, in rough order of how much they bother me:

- **`SUPABASE_KEY` is the service_role key**, so every query — auth included — runs as full
  admin and bypasses RLS. The per-request JWT client is already in place for when this moves
  to the anon key and RLS is actually enforced.
- **`/ingestion` is unauthenticated** and takes a free-text namespace, so it isn't tenant-scoped
  the way the booking tools are.
- **No conversation memory across requests.** The graph is rebuilt per request with a fresh
  `InMemorySaver` and a constant `thread_id`, so the checkpointer buys nothing between HTTP
  calls; each query starts cold.
- **No deployment endpoints.** Publish/unpublish and the public slug live in browser storage,
  so `/c/:slug` is a demo of the shape rather than a real multi-tenant deployment.
- **`delete_room_data`** in `services/booking_tools.py` is stubbed out and not wired to the
  agent.
- Model names are hardcoded in two separate files rather than configured.
- `self_docs/` describes intent as well as shipped work — e.g. the `clinics`/`appointments`
  skeleton in `may24.md` was never built. Verify against the code before relying on it.
