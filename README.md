# AI Workspace Operations Copilot

A multi-agent orchestration system that turns natural language into workspace
actions. An **Orchestrator Agent** (LangGraph) interprets each request and routes
it to specialized sub-agents — a **Knowledge Base Agent** for document Q&A (RAG
over Pinecone) and a **Booking Agent** for reservation slots on Supabase — then
composes a single answer.

The backend is a **FastAPI** service. The product frontend is **Receptix** — a
React 19 SPA in a [separate repo](../operations-copilot-js) that packages
everything as an "AI front desk" a business can publish for its customers: the
business signs up, uploads its documents, defines its bookable slots, and shares
one URL that its own customers chat with.

## Architecture

```
   POST /query · POST /query-agent (SSE)        POST /c/query-agent/{url_string}
        ← Authorization: Bearer <jwt>            ← public, anon client, must be published
                          \                     /
                           v                   v
                          +--------------------------+
                          |      Orchestrator        |  OpenRouter — GPT-OSS-120B
                          |       (LangGraph)        |  (structured output via instructor)
                          +--------------------------+
                             /                    \
                            v                      v
               +----------------+          +----------------+
               |   KB Agent     |          | Booking Agent  |
               | (Groq/GPT-OSS) |          | (Groq/GPT-OSS) |
               +----------------+          +----------------+
                       |                        |        \
                       v                        v         v
              +----------------+       +----------------+  +---------+
              |    Pinecone    |       |    Supabase    |  |  Brevo  |
              |  (Vector DB)   |       |  (PostgreSQL)  |  | (email) |
              +----------------+       +----------------+  +---------+
```

The graph is **one loop, not a pipeline**: all three nodes route through the
same conditional function (`tool_call_node`), so a sub-agent can hand straight to
another sub-agent without a return trip to the orchestrator. Sub-agent nodes
consume the `tool_calls` queue destructively, so it drains as the graph runs.
Two independent brakes stop it: the orchestrator's own `return_to_user` flag, and
`count > 3`, which forces the decision true regardless of what the LLM asked for.

The orchestrator **swallows its own exceptions** — on failure it returns a state
dict with only `return_to_user_decision: True` and an error string in
`response_to_user`, with no `tool_calls` key. That shape is load-bearing: the
eval graders detect it explicitly rather than scoring a crash as a graceful
give-up.

**Per-request identity** threads through `RunnableConfig`, so `user_id` and the
caller's Supabase client reach the tools without ever touching the LLM prompt.
Booking tools scope every query with `business_id = user_id`; KB tools resolve
the user's Pinecone namespace from a Supabase lookup table.

**Conversation memory** is a LangGraph Postgres checkpointer. `setup_graph`
returns an *uncompiled* builder; `dependencies.py` compiles it per request
against `PostgresSaver` (sync) or `AsyncPostgresSaver` (streaming), keyed on the
user's `links.thread_id`. Every node carries `RetryPolicy(max_attempts=3)`.

## Tech Stack

| Component        | Technology |
|------------------|------------|
| Orchestration    | LangGraph (state machine + conditional routing + Postgres checkpointer) |
| Orchestrator LLM | OpenRouter — `openai/gpt-oss-120b`, `instructor` (JSON_SCHEMA) |
| Sub-agent LLM    | Groq — `openai/gpt-oss-20b` (LangGraph ReAct agents) |
| Embeddings       | OpenRouter — `nvidia/llama-nemotron-embed-vl-1b-v2:free` (2048 → 1024-dim, Matryoshka truncation) |
| Vector Store     | Pinecone (serverless, cosine, per-user namespaces) |
| Database & Auth  | Supabase (PostgreSQL + GoTrue) |
| Transactional email | Brevo (booking confirmation links) |
| Tracing          | LangSmith (`wrap_openai` on the orchestrator client) |
| Web Framework    | FastAPI |
| Product Frontend | React 19 + Vite SPA (separate repo, GitHub Pages) |
| Dev UI           | Streamlit |
| Deployment       | Docker (Railway-ready) |

Model names are **hardcoded in two places**, not configured: the orchestrator
model is an argument in `agents/agent.py`, the sub-agent model is the `ChatGroq`
call in `agents/agent_config.py`.

## Project Structure

```
backend/
├── src/
│   ├── agents/                  # LangGraph state machine
│   │   ├── agent.py             # Orchestrator + sub-agent nodes + tool_call_node
│   │   ├── agent_config.py      # LLM clients, agent factories, system prompts
│   │   ├── graph.py             # StateGraph wiring (returns an uncompiled builder)
│   │   └── state.py             # TypedDict state + Pydantic output schemas
│   ├── KnowledgeBaseTool/       # RAG pipeline
│   │   ├── ingestion.py         # PDF → chunk → embed → upsert → record the ingestion
│   │   ├── retrieval.py         # Query embed + Pinecone similarity search
│   │   ├── embedding_config.py  # OpenRouter / Google / Ollama embedding fns
│   │   └── kb_tools.py          # LangChain @tool wrappers
│   ├── routes/
│   │   ├── inference.py         # POST /query, /query-agent (SSE streaming)
│   │   ├── ingestion.py         # POST /ingestion (authenticated PDF upload)
│   │   ├── auth.py              # POST /auth/signup, /auth/login
│   │   ├── frontend.py          # Dashboard + published-chat + webhook endpoints
│   │   └── eval.py              # Eval routes — commented out
│   ├── services/
│   │   ├── supabase_client.py   # Shared / anon / per-request / per-auth-call clients
│   │   ├── booking_tools.py     # Slot tools (scoped by business_id) + email send
│   │   ├── email_service.py     # Brevo transactional email + confirmation link
│   │   ├── auth_logic.py        # GoTrue signup/login + session dependency
│   │   └── supabase_db_functions.py  # All table reads/writes in one place
│   ├── utils/
│   │   ├── exceptions.py        # Ingestion / Retrieval / Authentication / BadRequest
│   │   ├── exception_handlers.py
│   │   └── postgresql_code.sql  # DDL, grants and RLS policies, kept as a record
│   ├── dependencies.py          # Per-request graph compile + inference runners
│   └── main.py                  # FastAPI app, CORS allowlist, router registration
├── evals/                       # Orchestrator regression suite (60 scenarios)
├── ui/
│   └── streamlit_ui.py          # Dev client for poking the API locally
├── self_docs/                   # Dated working notes and design decisions
├── tests/                       # Manual pytest-style scripts (gitignored)
├── Dockerfile
└── requirements.txt
```

## API Endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /auth/signup` | Public | Register user (email confirmation enabled) |
| `POST /auth/login` | Public | Returns `{user, session}` with JWT |
| `POST /query` | Bearer | Synchronous inference |
| `POST /query-agent` | Bearer | Streaming SSE — what the operator dashboard uses |
| `POST /ingestion` | Bearer | Upload PDF → chunk → embed → Pinecone (own namespace) |
| `GET /get-url` | Bearer | User's share URL + current publish status |
| `POST /set-publish` | Bearer | Set the publish flag on the user's `links` row |
| `GET /get-slots-data` | Bearer | List the business's slots |
| `POST /add-slot` | Bearer | Create an empty slot (`time_start`, `time_end`) |
| `POST /delete-slot` | Bearer | Delete a slot by `slot_id` |
| `GET /get-record-count` | Bearer | List ingested documents as `{ingestion_id, source_name}` |
| `POST /delete-ingested-source` | Bearer | Delete one source's vectors, then its `ingestions` row |
| `POST /c/query-agent/{url_string}` | Public | Published customer chat (SSE); refuses unless `published` is true |
| `GET /booking-confirmation/{verification_id}` | Public | Email webhook → `confirm_verification` RPC |

Auth uses Supabase GoTrue. `check_session_exists` validates the bearer token by
asking GoTrue directly (not a local JWT decode), so a revoked session or deleted
user is rejected immediately rather than staying trusted until token expiry.

The two public endpoints are deliberately anonymous: they are reached by a
business's *customers*, who have no account. Both use the anon-key client, and
`/c/query-agent/{url_string}` resolves the business from the share slug and
refuses to run unless that business has published.

`routes/eval.py` still exists, but **every `/eval/*` route in it is commented
out** — the router registers no paths. This is because, the system doesn't expose evaluations to the frontend side. The graders and the dataset
below are unaffected and still runnable, but the API endpoint is not exposed currently.

## Request lifecycles

**Chat.** `/query-agent` → validate JWT → build a per-request Supabase client
carrying that JWT → build the KB and booking agents bound to `user_id` and that
client → compile the graph against the Postgres checkpointer on the user's
`thread_id` → stream node updates as SSE events (`agent calls`, `knowledge base
agent`, `booking agent`, `final response`).

**Ingestion.** `/ingestion` → resolve the caller's namespace from
`pinecone_data_table` → write the upload to a temp dir → load and chunk the PDF →
embed → upsert to Pinecone in batches of 100 → record one row in `ingestions`
holding the filename, the `pinecone_data_table` PK, and the full list of vector
ids as JSONB → delete the temp dir.

**Deleting a source.** `/delete-ingested-source` → read the vector ids back out
of that `ingestions` row → resolve the namespace → `index.delete(ids=…,
namespace=…)` in batches of 1000 → only then delete the row. Vectors go first on
purpose: if Pinecone fails, the row survives with the ids still on record and the
delete can be retried, whereas dropping the row first would strand the vectors
with nothing pointing at them.

**Booking.** The booking agent assigns an existing slot with `update_room_data`
(times are set by the business and are not editable by the agent), which flips
the row to `status = 'pending'` and emails the occupier a link built from the
row's `verification_id`. Clicking it hits `/booking-confirmation/{verification_id}`,
which calls the `confirm_verification` RPC to move the row to `confirmed`. An
update that matches no row still returns 200 with an empty list, so the tool
raises on an empty result rather than silently "succeeding" and sending no email.

## Supabase clients — four kinds, deliberately

`services/supabase_client.py` exposes four accessors and they are not
interchangeable:

| Accessor | Key | Used by |
|---|---|---|
| `get_supabase_client()` | service_role | shared module-level client |
| `get_supabase_anon_client()` | anon | the two public endpoints |
| `get_supabase_client_with_token(jwt)` | service_role + `postgrest.auth(jwt)` | every authenticated request |
| `create_auth_client()` | service_role | one throwaway client per auth call |

`get_supabase_client_with_token` is what almost everything runs on: it calls
`client.postgrest.auth(access_token)`, so PostgREST sees the caller's JWT and
requests execute as `authenticated` with `auth.uid()` resolving and **RLS
enforced** — table grants and policies genuinely apply on these paths.

Auth errors travel as `AuthenticationError`, which carries the status code
Supabase reported. GoTrue answers 400 for bad credentials, which `sign_in`
rewrites to 401.

## Supabase Database

**`slots`** (booking data):

| Column | Type | Notes |
|---|---|---|
| `slotid` | uuid | Primary key |
| `business_id` | uuid | Owner's auth ID, every query scoped by it |
| `time_start` | timestamptz | Reservation start |
| `time_end` | timestamptz | Reservation end |
| `occupier_email` | citext | Who it's booked for |
| `status` | text | `pending` / `confirmed` |
| `verification_id` | uuid | Default `gen_random_uuid()`; the token in the confirmation link |

**`ingestions`** (one row per ingested document):

| Column | Type | Notes |
|---|---|---|
| `ing_id` | uuid | Primary key, default `gen_random_uuid()` |
| `source_name` | text | The uploaded filename |
| `pc_id` | uuid | FK → `pinecone_data_table` |
| `business_id` | uuid | FK → `auth.users` |
| `record_ids_json` | jsonb | `{"vector_ids_list": [...]}` — every Pinecone id for this source |

**`links`** (per-user share/publish state):

| Column | Type | Notes |
|---|---|---|
| `business_id` | uuid | Owner's auth ID, every query scoped by it |
| `thread_id` | text | LangGraph checkpoint thread for this user |
| `url` | text | Share URL slug for the published chat |
| `published` | boolean | Toggled via `/set-publish` |

**`pinecone_data_table`**: maps a business to its Pinecone namespace, populated by
a Supabase trigger on `auth.users` signup (namespace = email, business_id = user
id). Its PK is what `ingestions.pc_id` points at.

Plus a `confirm_verification` RPC, called by the booking-confirmation webhook.

DDL, grants and RLS policies are kept in `src/utils/postgresql_code.sql` as a
record of what was run; `supabase/` is gitignored and the dashboard remains the
source of truth. Note that PostgREST's `Prefer: return=representation` means an
insert or delete needs **SELECT** privilege too — a missing grant surfaces as
`42501 permission denied`, which is distinct from an RLS rejection ("new row
violates row-level security policy").

## Evaluation

**The eval layer is the regression suite.** `evals/orchestrator_dataset.json`
holds 60 hand-written scenarios across 5 categories, testing the orchestrator's
routing decisions in isolation — sub-agents, Pinecone and Supabase are never
touched, because the orchestrator node reads only `messages`,
`booking_agent_output`, `knowledge_base_agent_output` and `count`, all pinned by
the dataset.

| Category | Scenarios | What it asserts |
|---|---|---|
| `initial_routing` | 20 | which agents get queued on a fresh turn |
| `after_booking_response` | 10 | return to the user, or queue more calls |
| `after_kb_response` | 10 | same, from the KB side |
| `empty_agent_response` | 10 | tool calls **and** the return decision together |
| `irrelevant` | 10 | returns to the user with a non-empty `response_to_user` |

`expected.decisions` is a **list of acceptable decisions**, not one golden
answer — routing is legitimately non-deterministic and several scenarios have
more than one defensible next step. Agent names are compared as sets; the
free-form `argument` string is never graded.

Each category is one LLM call per scenario, so a 20-scenario run takes a couple
of minutes. The HTTP routes are commented out, so run the graders
directly:

```bash
python -c "
from evals.evaluation_engine import load_scenarios, run_initial_routing
user = {'id': '<uuid>', 'access_token': '<jwt>'}
status, results = run_initial_routing(load_scenarios('initial_routing'), user)
print(sum(status), '/', len(status))
"
```

`evaluation_engine.py` bootstraps its own imports (inserts `src/` on `sys.path`,
loads `.env` from the repo root) because it lives outside `src/`.

`tests/` is gitignored and holds manual scripts, not a maintained suite. A bare
`pytest` collects nothing — the files are named `*_testing.py`, which doesn't
match the default `test_*.py` pattern. Naming them explicitly does run:

```bash
python -m pytest tests/frontend_testing.py tests/graph_testing.py \
                 tests/agent_config_testing.py tests/agent_workflow_testing.py
# 11 passed
```

## Running Locally

```bash
pip install -r requirements.txt

# The API — must run from src/ (see Import layout below)
cd src && uvicorn main:app --reload    # http://localhost:8000, docs at /docs

# Streamlit dev UI
streamlit run ui/streamlit_ui.py        # expects the API on localhost:8000

# Docker — runs uvicorn from src/ and binds $PORT (default 3000)
docker build -t ops-copilot . && docker run -p 8000:3000 --env-file .env ops-copilot
```

Environment: `.env` with keys for OpenRouter, Groq, Pinecone, Supabase
(`SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_ANON_KEY`), Brevo, `INDEX_URL_PINECONE`,
and `DATABASE_URL` for the Postgres checkpointer.

**Import layout.** Modules import each other as `from agents…`, `from services…`,
`from routes…` — *not* `src.agents…`. So `src/` must be on the path: either run
from inside `src/`, or set `PYTHONPATH=src` in the environment. The
`PYTHONPATH=src` line inside `.env` is read by `python-dotenv` at runtime and
does **not** affect module resolution for the interpreter that is already
starting up.

## Frontend (Receptix)

The product frontend lives in [`../operations-copilot-js`](https://github.com/striderr1o1/operations-copilot-js)
— a **React 19 + Vite** SPA deployed to GitHub Pages:

| Route | What it is |
|---|---|
| `/` | Marketing home (hero, how-it-works, pricing, contact) |
| `/get-started`, `/login` | Signup/login against `/auth/*` (single page, mode toggle) |
| `/dashboard/chatbot` | Operator chat with streaming SSE, reasoning blocks, publish switch |
| `/dashboard/ingestion` | Drag-and-drop PDF upload, plus the ingested-document list with per-row delete |
| `/dashboard/check-slots` | View, add and delete bookable slots |
| `/c/:slug` | Published customer-facing chat (hidden reasoning) |

Frontend–backend communication:
- Session stored in `localStorage` (`receptix.session`); `api.js` attaches
  `Authorization: Bearer …` to every call
- API base resolved from `?api=` query param, then `VITE_API_BASE`, then the
  deployed default
- Dev server on port 5173; new origins must be added by hand to the CORS
  allowlist hardcoded in `src/main.py`
