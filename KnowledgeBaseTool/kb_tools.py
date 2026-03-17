from .ingestion import Ingestion
from .retrieval import Retrieval


def ingest_documents(documents_list):
    """Ingestion documents in this function as a list when 
    you get a list of documents to ingest"""
    ingestion_obj = Ingestion()
    for doc_path in documents_list:
        ingestion_obj.ingest_document(doc_path)
    return
    
def retrieve_documents(query):
    """retrieve relevant documents by putting the query in
    this function"""
    retrieval_obj = Retrieval()
    results =retrieval_obj.retrieve(query)
    return results
