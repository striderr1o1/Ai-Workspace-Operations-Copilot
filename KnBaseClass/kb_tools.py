from ingestion import ingestion
from retrieval import retrieval


class knowledge_base_functions:
    def __init__(self):
        self.ingestion_obj = None
        self.retrieval_obj = None
        return

    def ingest_documents(self, documents_list):
        self.ingestion_obj = ingestion()
        for doc_path in documents_list:
            self.ingestion_obj.ingest_document(doc_path)
        return
    
    def retrieve_documents(self, query):
        self.retrieval_obj = retrieval()
        results = self.retrieval_obj.retrieve(query)
        return results


# ingestion test
list = ['NexaCore_Organization_Report.pdf', 'resume2-10.pdf']
#kb_tools = knowledge_base_functions()
#kb_tools.ingest_documents(list)

# retrieval test
#knowledge_base_tools = knowledge_base_functions()
#knowledge_base_tools.retrieve_documents('enter query...')