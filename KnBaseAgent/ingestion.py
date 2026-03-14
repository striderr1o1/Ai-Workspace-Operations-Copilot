#ingestion class
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()

class ingestion:
    def __init__(self, filepath):
        self.filepath = filepath
        self.loader = PyPDFLoader(self.filepath)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap = 100)
        self.embedding = OllamaEmbeddings(
            model=os.environ.get("EMBEDDING_MODEL")
        )

    def ingest_document(self):
        doc = self._load_document()
        chunks = self._create_chunks(doc) 
        str_chunks = self._convert_doc_chunks_to_str(chunks)
        self._create_embeddings_from_chunks(str_chunks)
        return 

    def _load_document(self):
        pdf_docs = self.loader.load()
        return pdf_docs

    def _create_chunks(self, document_text):
        chunks = self.text_splitter.split_documents(document_text)
        return chunks

    def _convert_doc_chunks_to_str(self, chunks):
        str_chunks = []
        for chunk in chunks:
            string_chunk = str(chunk)
            str_chunks.append(string_chunk)
        return str_chunks

    def _create_embeddings_from_chunks(self, text_chunks):
        embeddings = self.embedding.embed_documents(text_chunks) 
        return

    # need to store in vector database