# AI Workspace Operations Copilot

A Multi-Agent Orchestration system built on top of LangGraph, utilizing LLMs, vector databases, and REST APIs to provide intelligent workspace management through natural language.

The system uses an orchestrator agent that routes user queries to specialized sub-agents — a **Knowledge Base Agent** for document Q&A (RAG) and a **Booking Agent** for room reservation management.

## Architecture

```
                         POST /query
                             |
                             v
                     +---------------+
                     |  Orchestrator  |  (OpenRouter - GPT-OSS-120B)
                     +---------------+
                        /         \
                       v           v
          +----------------+   +----------------+
          |  KB Agent      |   | Booking Agent  |
          |  (Groq/Qwen3)  |   | (Groq/Qwen3)  |
          +----------------+   +----------------+
              |                      |
              v                      v
     +--------------+        +-------------+
     |   Pinecone   |        |  Supabase   |
     | (Vector DB)  |        | (PostgreSQL)|
     +--------------+        +-------------+
```

**Query Flow:**
1. User submits a question via the `/query` endpoint
2. The orchestrator agent analyzes intent and routes to the appropriate sub-agent
3. The sub-agent processes the request using its tools (vector search or database ops)
4. Results flow back through the orchestrator, which composes the final response

**Ingestion Flow:**
1. User uploads a PDF via the `/ingestion` endpoint with a namespace
2. The PDF is split into chunks (1000 chars, 200 overlap)
3. Chunks are embedded using Ollama (`mxbai-embed-large`, 1024 dimensions)
4. Vectors are stored in Pinecone under the given namespace

## Tech Stack

| Component | Technology |
|---|---|
| Orchestration | LangGraph (state machine + conditional routing) |
| Orchestrator LLM | OpenRouter (GPT-OSS-120B) |
| Sub-agent LLM | Groq (Qwen3-32B, temperature=0) |
| Embeddings | Ollama (mxbai-embed-large, 1024-dim) |
| Vector Store | Pinecone (serverless, cosine similarity) |
| Database | Supabase (PostgreSQL) |
| Web Framework | FastAPI |
| Observability | LangSmith (optional) |

## Project Structure

```
backend/
├── src/
│   ├── agents/
│   │   ├── agent.py           # Agentic workflow orchestration
│   │   ├── agent_config.py    # Agent initialization and LLM config
│   │   ├── graph.py           # LangGraph state machine compilation
│   │   └── state.py           # State schema and Pydantic models
│   ├── KnowledgeBaseTool/
│   │   ├── ingestion.py       # PDF loading, chunking, embedding, Pinecone upsert
│   │   ├── retrieval.py       # Query embedding + Pinecone similarity search
│   │   └── kb_tools.py        # LangChain tool wrappers
│   ├── services/
│   │   └── supabase_client.py # Supabase room CRUD operations
│   ├── utils/
│   │   └── exceptions.py      # Custom exception classes
│   ├── main.py                # FastAPI app and route definitions
│   └── dependencies.py        # Dependency initialization
├── tests/
│   └── bktools_tests.py       # Retrieval tests
├── requirements.txt
└── .env
```

## API Endpoints

### `POST /query`

Send a natural language query to the agent system.

**Request body:** plain string

**Response:** orchestrated agent response

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '"What rooms are available today?"'
```

### `POST /ingestion`

Upload a PDF document to be ingested into the knowledge base.

**Parameters:**
- `file` — PDF file upload
- `namespace_name` — Pinecone namespace to store the document under

```bash
curl -X POST http://localhost:8000/ingestion \
  -F "file=@document.pdf" \
  -F "namespace_name=my-docs"
```

## Get Started

### Prerequisites

- Python 3.11
- [Ollama](https://ollama.com/) running locally with the embedding model pulled
- Pinecone account
- Groq API key
- OpenRouter API key
- Supabase project

### Installation

1. Pull the embedding model:
```bash
ollama pull mxbai-embed-large:latest
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```
EMBEDDING_MODEL=mxbai-embed-large:latest
PINECONE_API_KEY=
PINECONE_INDEX_NAME=
INDEX_URL_PINECONE=

GROQ_API_KEY=
OPENROUTER_API_KEY=

SUPABASE_URL=
SUPABASE_KEY=          # service_role key recommended to bypass RLS

OLLAMA_API_KEY=
PYTHONPATH=

# Optional - LangSmith observability
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
```

4. Set up a Supabase `rooms` table with columns: `room_id`, `occupier_name`, `occupied_status`, `start_time`, `end_time`, `reservation_date`.

### Run

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.
