from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
load_dotenv()

class Ingestion:
    def __init__(self): #configuration
        self.filepath = None
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap = 100)
        self.embedding = OllamaEmbeddings(
            model=os.environ.get("EMBEDDING_MODEL")
        )
        self.pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
        self.index_name = os.environ.get('PINECONE_INDEX_NAME')

    def ingest_document(self, filepath):
         #main function
        self.filepath = filepath
        doc = self._load_document()
        chunks = self._create_chunks(doc) 
        str_chunks = self._convert_doc_chunks_to_str(chunks)
        embeddings_list = self._create_embeddings_from_chunks(str_chunks)
        self._create_index()
        vectors_list = self._preparing_ingestions(embeddings_list, str_chunks)
        self._store_in_vectordb(vectors_list)
        return 

    def _load_document(self): #load the document
        self.loader = PyPDFLoader(self.filepath)
        pdf_docs = self.loader.load()
        return pdf_docs

    def _create_chunks(self, document_text):# create the chunks
        chunks = self.text_splitter.split_documents(document_text)
        return chunks

    def _convert_doc_chunks_to_str(self, chunks): #convert chunks to string type chunks
        str_chunks = []
        for chunk in chunks:
            string_chunk = str(chunk)
            str_chunks.append(string_chunk)
        return str_chunks

    def _create_embeddings_from_chunks(self, text_chunks): # create embeddings out of string chunks
        embeddings = self.embedding.embed_documents(text_chunks) 
        if not embeddings:
            self.logger.error('[x] failed to create embeddings')
            return
        return embeddings

    def _create_index(self): #initialize index if not already
        if not self.pc.has_index(self.index_name):
            self.pc.create_index(
                name=self.index_name,
                vector_type="dense",
                dimension=1024, #according to model
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                ),
                deletion_protection="disabled",
                tags={
                    "environment": "development"
                }
            )

    def _preparing_ingestions(self, embeddings_list, string_chunks): #prepare vectors for ingestion
        length_of_embeddings = len(embeddings_list)
        length_of_chunkslist = len(string_chunks)
        vectors_list = []
        if length_of_chunkslist == length_of_embeddings:
            for i in range(0, length_of_chunkslist):
                vector = {
                    'id': f'document1#chunk: {i}',
                    "values": embeddings_list[i],
                    "metadata": {
                            "document_id": f'document1#chunk: {i}',
                            "document_title": "resume",
                            "chunk_number": i+1,
                            "chunk_text": string_chunks[i],
                            "document_type": ""
                    }
                }
                vectors_list.append(vector)
        return vectors_list

        
    def _store_in_vectordb(self, vectors_list): #upsert in pinecone vector store
        index = self.pc.Index(host=os.environ.get('INDEX_URL_PINECONE'))
        index.upsert(
            namespace = "test-resume",
            vectors = vectors_list
        )

        return
# need to add error handling