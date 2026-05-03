from .ingestion import Ingestion
from .retrieval import Retrieval
from langchain.tools import tool
from langchain_core.tools import ToolException
from pinecone import Pinecone
import os
def ingest_documents(documents_list, namespace):
    """Ingestion documents in this function as a list when 
    you get a list of documents to ingest"""
    try:
        ingestion_obj = Ingestion()
        for doc_path in documents_list:
            ingestion_obj.ingest_document(doc_path, namespace)
        return
    except Exception as e:
        raise ToolException(f"Error in using tool: {e}")

@tool    
def retrieve_documents(query, namespace_name):
    """retrieve relevant documents by putting the query in
    this function, use one namespace at a time """
    try:
        retrieval_obj = Retrieval()
        results =retrieval_obj.retrieve(query, namespace_name)
        return results
    except Exception as e:
        raise ToolException(f"Error in using tool: {e}")


@tool
def get_all_namespaces():
    """use this function to get namespaces names"""
    pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
    index = pc.Index(host=os.environ.get('INDEX_URL_PINECONE'))
    stats = index.describe_index_stats()
    namespaces = list(stats.namespaces.keys())
    return namespaces
