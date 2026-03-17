from ingestion import ingestion
from retrieval import retrieval


def ingest_documents(documents_list):
    ingestion_obj = ingestion()
    for doc_path in documents_list:
        ingestion_obj.ingest_document(doc_path)
    return
    
def retrieve_documents(query):
    retrieval_obj = retrieval()
    results =retrieval_obj.retrieve(query)
    return results

ingest_documents(['NexaCore_Organization_Report.pdf'])