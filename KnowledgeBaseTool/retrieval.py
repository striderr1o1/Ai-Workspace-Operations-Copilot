import os
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from utils.exceptions import RetrievalError
load_dotenv()
class Retrieval:
    def __init__(self):
        self.pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
        self.index_name = os.environ.get('PINECONE_INDEX_NAME')
        self.embedding = OllamaEmbeddings(
            model=os.environ.get("EMBEDDING_MODEL")
        )
        return

    def retrieve(self, query):
        embeddings = self._create_embeddings(query)
        results = self._get_results(embeddings)
        return results
    
    def _create_embeddings(self, query):
        try:
            embeddings = self.embedding.embed_query(query) 
            return embeddings
        except Exception:
            raise RetrievalError('retrieval.py: error in creating retrieval embeddings')
    def _get_results(self, embeddings):
        try:
            index = self.pc.Index(host=os.environ.get('INDEX_URL_PINECONE'))
       
            results = index.query(
                namespace='test-resume',
                vector=embeddings, 
                top_k=7,
                include_metadata=True,
                include_values=False
            )
 
            return results
        except Exception:
            raise RetrievalError('retrieval.py: Error in getting retrieval results')