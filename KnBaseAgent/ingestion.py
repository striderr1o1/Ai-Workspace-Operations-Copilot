#ingestion class
from langchain_community.document_loaders import PyPDFLoader

class ingestion:
    def __init__(self, filepath):
        self.filepath = filepath

    def ingest_document(self):

        return 