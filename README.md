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
│   │   └── ingestion.py        # /ingestion (PDF upload)
│   ├── services/
│   │   └── supabase_client.py  # Room CRUD tools (fetch/insert/update)
│   ├── utils/
│   │   └── exceptions.py       # Custom exception classes
│   ├── dependencies.py         # Graph assembly + inference runners
│   └── main.py                 # FastAPI app, CORS, router registration
├── ui/
│   └── streamlit_ui.py         # Streamlit chat client
├── tests/                      # pytest suite (see tests/TESTING_GUIDE.md)
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

### Run the Streamlit UI

With the API running, in a separate terminal:

```bash
streamlit run ui/streamlit_ui.py
```

The UI talks to the backend at `http://localhost:8000` (configurable via `API_BASE_URL` in `ui/streamlit_ui.py`).

### Run with Docker

```bash
docker build -t ops-copilot .
docker run -p 8000:3000 --env-file .env ops-copilot
```

The container runs uvicorn from `src/` and binds to `$PORT` (defaults to `3000`), making it deployable to Railway and similar platforms.

## Testing

The `tests/` directory contains a pytest suite covering exceptions, state, ingestion, retrieval, the agent graph, and the API. See `tests/TESTING_GUIDE.md` for details.

```bash
pytest
```
