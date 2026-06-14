import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from utils.exceptions import RetrievalError
from .embedding_config import get_openrouter_embeddings
load_dotenv()
class Retrieval:
    def __init__(self):
        self.pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
        self.index_name = os.environ.get('PINECONE_INDEX_NAME')
        return

    def retrieve(self, query, namespace):
        embeddings = self._create_embeddings(query)
        results = self._get_results(embeddings, namespace)
        return results
    def _create_embeddings(self, query):
        try:
            # Embed the query with the SAME model used at ingestion so the
            # query vector lives in the same space as the stored chunks.
            # get_openrouter_embeddings takes a list and returns one vector
            # per item, so pass the query as a single-element list and unwrap.
            embeddings = get_openrouter_embeddings([query])[0]
            return embeddings
        except Exception:
            raise RetrievalError('retrieval.py: error in creating retrieval embeddings')
    def _get_results(self, embeddings, namespace):
        try:
            index = self.pc.Index(host=os.environ.get('INDEX_URL_PINECONE'))
       
            results = index.query(
                namespace=namespace,
                vector=embeddings, 
                top_k=5,
                include_metadata=True,
                include_values=False
            )
 
            return results
        except Exception:
            raise RetrievalError('retrieval.py: Error in getting retrieval results')


