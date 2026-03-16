from ingestion import ingestion
import logging
from retrieval import retrieval
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

class knowledge_base_agent:
    def __init__(self):
        self.ingestion_obj = None
        self.retrieval_obj = None
        return

    def ingest_documents(self, documents_list):
        self.ingestion_obj = ingestion(logging)
        for doc_path in documents_list:
            self.ingestion_obj.ingest_document(doc_path)
        return
#ingestion_obj = ingestion("NexaCore_Organization_Report.pdf", logging=logging)
#ingestion_obj.ingest_document()

#retrieval_obj = retrieval(logging=logging)
#retrieval_obj.retrieve('who is Muhammad Mustafa Noman')

list = ['NexaCore_Organization_Report.pdf', 'resume2-10.pdf']

agent = knowledge_base_agent()
agent.ingest_documents(list)