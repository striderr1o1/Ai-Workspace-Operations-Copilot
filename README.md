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

## Implementation Thought Process:
First I implemented the Ingestion class. In that class, I implemented all the ingestion related functions. I faced a few problems, for example:
- the chunks were not in string format and the next function was not accepting it, so i had to convert them to string manually using a for loop
- I had to setup my own embedding model running on the local machine with pinecone. For that I referred to the pinecone docs and eventually found a way. I also had to arrange the embeddings in the correct format for pinecone, that I did by creating the _preparing_ingestions function in the ingestion.py. Next, I had these ingested in the vector store.
- While trying to setup ingestion, I also learned about sparse and dense vectors. Upon a quick google search, I got to know that dense vectors are more suitable for semantic use case, so I used that format.
- I also faced an issue in which the dimensions set in the pinecone index mismatched those of the embedding model. I initially thought that the embedding model mxbai-embed-large:latest uses 512 dimensions, so I set it accordingly in the index creation function, but on facing the error, I had to set it to 1024.
