# Ai Workspace Operations Copilot:

## Get Started:
- Install Ollama mxbai-embed-large:latest embedding model
- Get the pinecone API key
- Get GROQ API key
- Install the requirements (python 3.11)
```bash
pip install -r requirements.txt
```
- Setup the .env file:

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
```

-  test ingestion/retrieval by running and adjusting changes in the file:
```bash
python KnBaseClass/kb_tools.py
```