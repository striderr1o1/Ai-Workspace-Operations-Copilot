import os
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
load_dotenv()
class retrieval:
    def __init__(self, logging):
        self.logger = logging.getLogger(__name__)
        self.pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
        self.index_name = os.environ.get('PINECONE_INDEX_NAME')
        self.embedding = OllamaEmbeddings(
            model=os.environ.get("EMBEDDING_MODEL")
        )
        return

    def retrieve(self, query):
        embeddings = self._create_embeddings(query)
        results = self._get_results(embeddings)
        print(results)
        return
    
    def _create_embeddings(self, query):
        embeddings = self.embedding.embed_query(query) 
        return embeddings
    def _get_results(self, embeddings):
        index = self.pc.Index(host=os.environ.get('INDEX_URL_PINECONE'))
       
        results = index.query(
            namespace='test-resume',
            vector=embeddings, 
            top_k=3,
            include_metadata=True,
            include_values=False
        )
 
        return results