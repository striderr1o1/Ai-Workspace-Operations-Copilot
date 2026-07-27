# AI Workspace Operations Copilot

A multi-agent orchestration system built on **LangGraph** that turns natural language into workspace actions. An orchestrator agent interprets each request and routes it to specialized sub-agents — a **Knowledge Base Agent** for document Q&A (RAG) and a **Booking Agent** for meeting-room reservations — then composes a single, coherent answer for the user.

The backend is a **FastAPI** service exposing synchronous and streaming query endpoints plus a document-ingestion endpoint. A **Streamlit** chat UI is included for local testing and demos.

## Architecture

```
                    POST /query  ·  POST /query-agent (SSE)
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
               |  (Groq/Qwen3)  |   |  (Groq/Qwen3)  |
               +----------------+   +----------------+
                       |                    |
                       v                    v
              +----------------+    +----------------+
              |    Pinecone    |    |    Supabase    |
              |  (Vector DB)   |    |  (PostgreSQL)  |
              +----------------+    +----------------+
```

The orchestrator and sub-agents share a single LangGraph state machine. The graph loops between the orchestrator and the sub-agents until the orchestrator decides to return to the user (or a safety counter caps the number of hops), so multi-step requests that touch both the knowledge base and the booking system are handled in one invocation.

**Query flow**
1. A user submits a natural-language query to `/query` (synchronous) or `/query-agent` (streaming SSE).
2. The orchestrator analyzes intent and emits structured tool calls naming the sub-agent(s) to invoke.
3. Each sub-agent runs its own tools — Pinecone vector search for the KB Agent, Supabase CRUD for the Booking Agent — and returns a result.
4. Control returns to the orchestrator, which either dispatches another step or finalizes a summary for the user. A hop counter bounds the loop to keep runs terminating.

**Ingestion flow**
1. A PDF is uploaded to `/ingestion` together with a target namespace.
2. The document is split into chunks (1000 chars, 200-char overlap).
3. Chunks are embedded with OpenRouter (`nvidia/llama-nemotron-embed-vl`), truncated to 1024 dimensions (Matryoshka), and batched.
4. Vectors are upserted into Pinecone under the given namespace.

## Tech Stack

| Component         | Technology                                                        |
|-------------------|-------------------------------------------------------------------|
| Orchestration     | LangGraph (state machine + conditional routing, retry policies)   |
| Orchestrator LLM  | OpenRouter — `openai/gpt-oss-120b`, structured output via `instructor` |
| Sub-agent LLM     | Groq — `qwen/qwen3-32b`, `temperature=0`                          |
| Embeddings        | OpenRouter — `nvidia/llama-nemotron-embed-vl` (1024-dim, Matryoshka-truncated) |
| Vector Store      | Pinecone (serverless, cosine, namespaced)                         |
| Database          | Supabase (PostgreSQL)                                             |
| Web Framework     | FastAPI                                                           |
| Demo UI           | Streamlit                                                         |
| Observability     | LangSmith (optional)                                              |
| Deployment        | Docker (Railway-ready, binds `$PORT`)                            |

> **Note on embeddings:** ingestion and retrieval must use the *same* embedding model so query and document vectors share a space. The codebase currently uses OpenRouter; Google Gemini (`gemini-embedding-001`) and local Ollama (`mxbai-embed-large`) implementations are also present in `embedding_config.py` and can be swapped in. All three are configured to output 1024-dim vectors to match the Pinecone index.

## Project Structure

```
backend/
├── src/
│   ├── agents/
│   │   ├── agent.py            # Orchestrator + sub-agent node logic
│   │   ├── agent_config.py     # LLM clients, agent factories, system prompt
│   │   ├── graph.py            # LangGraph state machine wiring
│   │   └── state.py            # TypedDict graph state + Pydantic schemas
│   ├── KnowledgeBaseTool/
│   │   ├── ingestion.py        # PDF load → chunk → embed → Pinecone upsert
│   │   ├── retrieval.py        # Query embed + Pinecone similarity search
│   │   ├── embedding_config.py # OpenRouter / Google / Ollama embedding fns
│   │   └── kb_tools.py         # LangChain tool wrappers (ingest, retrieve, namespaces)
│   ├── routes/
│   │   ├── inference.py        # /query and /query-agent (streaming)
│   │   ├── ingestion.py        # /ingestion (PDF upload)
│   │   └── eval.py             # /eval/* evaluation endpoints
│   ├── services/
│   │   └── supabase_client.py  # Room CRUD tools (fetch/insert/update)
│   ├── utils/
│   │   └── exceptions.py       # Custom exception classes
│   ├── dependencies.py         # Graph assembly + inference runners
│   └── main.py                 # FastAPI app, CORS, router registration
├── evals/
│   ├── evaluation_engine.py        # Scenario loader + graders
│   └── orchestrator_dataset.json   # 60 hand-written orchestrator scenarios
├── ui/
│   └── streamlit_ui.py         # Streamlit chat client
├── tests/                      # tool-level tests (not tracked in git)
├── Dockerfile
├── requirements.txt
└── .env
```

## API Endpoints

### `POST /query`

Run a query synchronously and return the final orchestrated result.

**Request body**
```json
{ "query": "What rooms are available today?" }
```

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What rooms are available today?"}'
```

### `POST /query-agent`

Same input as `/query`, but streams progress as **Server-Sent Events** — emitting `agent calls`, `knowledge base agent`, `booking agent`, and `final response` events as the graph executes. Used by the Streamlit UI for live status.

```bash
curl -N -X POST http://localhost:8000/query-agent \
  -H "Content-Type: application/json" \
  -d '{"query": "Book room 3 for Sarah from 2pm to 3pm today"}'
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

Return `orchestrator_dataset.json` along with a per-category index (`category`, `endpoint`, `count`). Read-only and cheap — it runs no evaluation. The frontend uses it to populate the scenario dropdown and preview the cases before running them.

### `POST /eval/{category}`

Run the orchestrator evaluation for one scenario category — see [Evaluation](#evaluation). One endpoint per category: `initial-routing`, `after-booking-response`, `after-kb-response`, `empty-agent-response`, `irrelevant`.

```bash
curl -X POST http://localhost:8000/eval/initial-routing
```

All five return the same report shape, so a caller can render any category without knowing which assertion that category's grader made:

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

`actual` is the orchestrator's raw state delta, unmodified. When the orchestrator swallows an exception it has no `tool_calls` key at all, which the graders already score as a failure — the report passes that through rather than hiding it. Each call issues one LLM request per scenario, so a 20-scenario category takes a couple of minutes.

## Frontend

The browser client lives in a separate repo, [`operations-copilot-js`](https://github.com/striderr1o1/operations-copilot-js) — static HTML/CSS/JS, no build step. `index.html` is the chat and ingestion view; `evals.html` drives the endpoints above: pick a category, preview its scenarios, hit play, and read the pass/fail table. Both pages point at the deployed API by default; append `?api=http://127.0.0.1:8000` to run against a local server. Serve the pages from port 3000 (`python3 -m http.server 3000`) so the browser's origin is one the CORS allowlist in `src/main.py` already accepts.

## Evaluation

Routing is the part of this system most likely to regress silently: a prompt tweak that improves one kind of request can quietly break another, and nothing crashes when it does. `evals/` exists to catch that.

**What is measured.** `orchestrator_dataset.json` holds 60 hand-written scenarios that each pin down the exact graph state the orchestrator node sees, then check the single decision it makes from that state. Sub-agents are never invoked — the engine calls `agentic_workflow.orchestrator(state)` directly, since that method reads only `messages`, `booking_agent_output`, `knowledge_base_agent_output`, and `count`. One LLM call per scenario, no database or vector-store access, and the code under test is the production node rather than a copy of it.

**Categories**

| Category                 | N  | Question it answers                                                |
|--------------------------|----|--------------------------------------------------------------------|
| `initial_routing`        | 20 | Straight after START, does it pick the right sub-agent?            |
| `after_booking_response` | 10 | Booking output is present — return to the user, or keep going?     |
| `after_kb_response`      | 10 | Knowledge base output is present — same question                   |
| `empty_agent_response`   | 10 | An agent was called and returned nothing. Retry, or fail honestly? |
| `irrelevant`             | 10 | Greetings and out-of-scope asks that no sub-agent should handle    |

**How scenarios are graded.** `expected.decisions` is a *list* of acceptable decisions, not a single golden answer — routing isn't deterministic and several scenarios have more than one defensible next step. Scenario 17 ("Is room 2 free at 3pm? Also, what's the meeting room usage policy?") accepts queueing both agents or starting with either one, because all three lead to a correct final answer. A scenario passes if the produced decision matches any entry.

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

`tool_calls` lists just the agent names; the free-form `argument` the orchestrator sends each agent is not graded. Agent names are compared as a set, so ordering within a single decision doesn't matter. `reference_response`, where non-empty, is a known-good reply kept for judging response relevancy.

**Failure modes deliberately covered.** Beyond happy-path routing, the dataset targets the ways an agent is dishonest rather than broken:

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

   # Database
   SUPABASE_URL=
   SUPABASE_KEY=               # service_role key recommended (bypasses RLS)

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

3. Create the Supabase `rooms` table with columns:

   | Column             | Type   | Notes                          |
   |--------------------|--------|--------------------------------|
   | `room_id`          | int4   | primary key                    |
   | `occupier_name`    | text   | name of the occupant           |
   | `occupied_status`  | bool   | whether the room is occupied   |
   | `start_time`       | time   | reservation start              |
   | `end_time`         | time   | reservation end                |
   | `reservation_date` | date   | reservation date               |

### Run the API

```bash
cd src
uvicorn main:app --reload
```

The API is served at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### Run with Docker

```bash
docker build -t ops-copilot .
docker run -p 8000:3000 --env-file .env ops-copilot
```

The container runs uvicorn from `src/` and binds to `$PORT` (defaults to `3000`), making it deployable to Railway and similar platforms.
