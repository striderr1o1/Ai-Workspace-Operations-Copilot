# Ai Workspace Operations Copilot:

## Get Started:
- Install Ollama mxbai-embed-large:latest embedding model
- Get the pinecone API key
- Get GROQ API key
- Install the requirements (python 3.11)
- Setup the .env file:
- Get the relevant api keys (groq and openrouter)
- setup the supabase database, connect the url and the key.
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

```
EMBEDDING_MODEL = mxbai-embed-large:latest
PINECONE_API_KEY =
PINECONE_INDEX_NAME =
INDEX_URL_PINECONE =

export LANGSMITH_TRACING=true
export LANGSMITH_ENDPOINT=
export LANGSMITH_API_KEY=
export LANGSMITH_PROJECT=""
GROQ_API_KEY =
export PYTHONPATH=
OLLAMA_API_KEY=
OPENROUTER_API_KEY=
SUPABASE_URL=
SUPABASE_KEY= ( i used service_role key to by pass restrictions)
```

## Issues: 

There are some issues: 
- if orchestrator is passed back the output of the sub agents, it keeps on querying them and does not decided to end the loop, so at the moment, 'end' is hard-coded in the tool_calling_node. 


