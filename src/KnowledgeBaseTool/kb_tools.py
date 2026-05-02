from .ingestion import Ingestion
from .retrieval import Retrieval
from langchain.tools import tool
from langchain_core.tools import ToolException

@tool
def ingest_documents(documents_list):
    """Ingestion documents in this function as a list when 
    you get a list of documents to ingest"""
    try:
        ingestion_obj = Ingestion()
        for doc_path in documents_list:
            ingestion_obj.ingest_document(doc_path)
        return
    except Exception as e:
        raise ToolException(f"Error in using tool: {e}")

@tool    
def retrieve_documents(query):
    """retrieve relevant documents by putting the query in
    this function"""
    try:
        retrieval_obj = Retrieval()
        results =retrieval_obj.retrieve(query)
        return results
    except Exception as e:
        raise ToolException(f"Error in using tool: {e}")
