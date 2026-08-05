# AI Workspace Operations Copilot

> **🚧 Work in progress.** I'm actively building this — interfaces move, pieces
> documented in `self_docs/` are intent as much as shipped code, and known gaps
> are listed under [Project status](#project-status). This README is a snapshot
> of where the project is today.

A multi-agent orchestration system that turns natural language into workspace
actions. An **Orchestrator Agent** (LangGraph) interprets each request and routes
it to specialized sub-agents — a **Knowledge Base Agent** for document Q&A (RAG
over Pinecone) and a **Booking Agent** for reservation slots on Supabase — then
composes a single answer.

The backend is a **FastAPI** service. The product frontend is **Receptix** — a
React 19 SPA in a [separate repo](../operations-copilot-js) that packages
everything as an "AI front desk" a business can publish for its customers. A
**Supabase** database is being built alongside to handle auth, booking data, and
per-user namespace mappings.

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

The graph is **one loop, not a pipeline**: all three nodes route through the
same conditional function, so sub-agents can hand straight to each other without
returning to the orchestrator. A hop counter (`count > 3`) and the
orchestrator's own `return_to_user` flag prevent infinite loops.

**Per-request identity** threads through `RunnableConfig`, so `user_id` and JWT
reach tools without ever touching the LLM prompt. Booking tools create a
per-call Supabase client with the caller's JWT and scope every query with
`business_id = user_id`. KB tools resolve the user's Pinecone namespace from a
Supabase lookup table.

## Tech Stack

| Component        | Technology |
|------------------|------------|
| Orchestration    | LangGraph (state machine + conditional routing) |
| Orchestrator LLM | OpenRouter — `openai/gpt-oss-120b`, `instructor` (JSON_SCHEMA) |
| Sub-agent LLM    | Groq — `openai/gpt-oss-20b` |
| Embeddings       | OpenRouter — `nvidia/llama-nemotron-embed-vl` (1024-dim, Matryoshka) |
| Vector Store     | Pinecone (serverless, cosine, per-user namespaces) |
| Database & Auth  | Supabase (PostgreSQL + GoTrue) |
| Web Framework    | FastAPI |
| Product Frontend | React 19 + Vite SPA (separate repo, GitHub Pages) |
| Dev UI           | Streamlit |
| Deployment       | Docker (Railway-ready) |

## Project Structure

```
backend/
├── src/
│   ├── agents/                  # LangGraph state machine
│   │   ├── agent.py             # Orchestrator + sub-agent node logic
│   │   ├── agent_config.py      # LLM clients, factories, system prompt
│   │   ├── graph.py             # StateGraph wiring
│   │   └── state.py             # TypedDict state + Pydantic output schemas
│   ├── KnowledgeBaseTool/       # RAG pipeline
│   │   ├── ingestion.py         # PDF → chunk → embed → Pinecone upsert
│   │   ├── retrieval.py         # Query embed + Pinecone similarity search
│   │   ├── embedding_config.py  # OpenRouter / Google / Ollama embedding fns
│   │   └── kb_tools.py          # LangChain @tool wrappers
│   ├── routes/
│   │   ├── inference.py         # POST /query, /query-agent (SSE streaming)
│   │   ├── ingestion.py         # POST /ingestion (PDF upload)
│   │   ├── eval.py              # GET /eval/dataset, POST /eval/{category}
│   │   └── auth.py              # POST /auth/signup, /auth/login
│   ├── services/
│   │   ├── supabase_client.py   # Shared / per-request / per-auth-call clients
│   │   ├── booking_tools.py     # Slot CRUD tools (scoped by business_id)
│   │   ├── auth_logic.py        # GoTrue signup/login + session dependency
│   │   └── supabase_db_functions.py  # Namespace lookups
│   ├── utils/
│   │   ├── exceptions.py        # Ingestion / Retrieval / Authentication errors
│   │   └── exception_handlers.py
│   ├── dependencies.py          # Per-request graph assembly + inference runners
│   └── main.py                  # FastAPI app, CORS, router registration
├── evals/                       # Orchestrator regression suite (60 scenarios)
├── ui/
│   └── streamlit_ui.py          # Dev client for poking the API locally
├── self_docs/                   # Dated working notes and design decisions
├── tests/                       # Manual scripts (gitignored)
├── Dockerfile
└── requirements.txt
```

## API Endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /auth/signup` | Public | Register user (email confirmation enabled) |
| `POST /auth/login` | Public | Returns `{user, session}` with JWT |
| `POST /query` | Bearer | Synchronous inference |
| `POST /query-agent` | Bearer | Streaming SSE — what both frontends use |
| `POST /ingestion` | Public | Upload PDF → embed → Pinecone |
| `GET /eval/dataset` | Bearer | Return all 60 eval scenarios |
| `POST /eval/{category}` | Bearer | Run orchestrator evals for one category |

Auth uses Supabase GoTrue. `check_session_exists` validates the bearer token by
asking GoTrue directly (not local JWT decode), so revoked sessions are rejected
immediately.

## Frontend (Receptix)

The product frontend lives in [`../operations-copilot-js`](../operations-copilot-js)
— a **React 19 + Vite** SPA deployed to GitHub Pages. It packages the copilot as
a business-facing front desk:

| Route | What it is |
|---|---|
| `/` | Marketing home (hero, how-it-works, pricing, contact) |
| `/get-started`, `/login` | Signup/login against `/auth/*` (single page, mode toggle) |
| `/dashboard/chatbot` | Operator chat with streaming SSE, reasoning blocks, publish switch |
| `/dashboard/ingestion` | Drag-and-drop PDF upload (25 MB cap) |
| `/dashboard/evaluations` | Run eval categories, see pass/fail tables |
| `/c/:slug` | Published customer-facing chat (hidden reasoning) |

Frontend-backend communication:
- Session stored in `localStorage` (`receptix.session`); `api.js` attaches
  `Authorization: Bearer …` to every call
- API base resolved from `?api=` query param, then `VITE_API_BASE` env var,
  then `http://localhost:8000`
- Dev server on port 5173 (on the CORS allowlist in `main.py`)
- Publish state is currently **client-side only** (`localStorage`) — the
  backend has no deployment endpoints yet

## Supabase Database

The database is being built alongside the backend. Current schema:

**`slots` table** (booking data):
| Column | Type | Notes |
|---|---|---|
| `slotid` | uuid | Primary key |
| `business_id` | uuid | Owner's auth ID, every query scoped by it |
| `time_start` | timestamptz | Reservation start |
| `time_end` | timestamptz | Reservation end |
| `occupier_email` | citext | Who it's booked for |

**`pinecone_data_table`**: Maps user IDs to their Pinecone namespace. Populated
by a Supabase trigger on `auth.users` signup (namespace = email, business_id =
user id).

All DDL lives in the Supabase dashboard — `supabase/` is gitignored, so there's
no schema tracked in this repo.

## Evaluation

No pytest suite — `tests/` is gitignored manual scripts. The eval layer is the
regression suite.

`evals/orchestrator_dataset.json` has 60 hand-written scenarios across 5
categories testing the orchestrator's routing decisions in isolation (no
sub-agents, no DB calls). Each scenario calls `orchestrator(state)` directly and
compares the output against a list of acceptable decisions (routing isn't
deterministic).

## Running Locally

```bash
# Backend
pip install -r requirements.txt
cd src && uvicorn main:app --reload    # http://localhost:8000

# Streamlit dev UI
streamlit run ui/streamlit_ui.py        # expects API on localhost:8000

# Docker
docker build -t ops-copilot . && docker run -p 8000:3000 --env-file .env ops-copilot
```

Environment: `.env` with keys for OpenRouter, Groq, Pinecone, and Supabase.
`PYTHONPATH=src` must be set when running from the repo root.

## Project Status

What works end to end: signup/login, streaming chat routing between two
sub-agents, PDF ingestion into per-user Pinecone namespaces, per-user booking
data scoping, and the eval suite with a UI.

What I'm actively working on:

- **Supabase database schema** — building the tables, RLS policies, and
  triggers alongside the backend code
- **`SUPABASE_KEY` is the service_role key** — queries run as admin, bypassing
  RLS. The per-request JWT client infrastructure is ready for switching to the
  anon key
- **`/ingestion` is unauthenticated** — not tenant-scoped like booking tools
- **No conversation memory** — graph rebuilt per request with fresh
  `InMemorySaver`, so each query starts cold
- **No deployment endpoints** — publish/unpublish and slug are in browser
  storage, not the backend
- **`delete_room_data`** is stubbed and not wired to the agent
- **Model names hardcoded** in two files rather than configured
