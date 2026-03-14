#ingestion class
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class ingestion:
    def __init__(self, filepath):
        self.filepath = filepath
        self.loader = PyPDFLoader(self.filepath)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap = 100)

    def ingest_document(self):
        doc = self._load_document()
        texts = self._create_chunks(doc) 
        return 

    def _load_document(self):
        pdf_docs = self.loader.load()
        return pdf_docs

    def _create_chunks(self, document_text):
        texts = self.text_splitter.split_documents(document_text)
        return texts