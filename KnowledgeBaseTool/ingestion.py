from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from utils.exceptions import IngestionError
load_dotenv()

class Ingestion:
    def __init__(self): #configuration
        self.filepath = None
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap = 200)
        self.embedding = OllamaEmbeddings(
            model=os.environ.get("EMBEDDING_MODEL")
        )
        self.pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
        self.index_name = os.environ.get('PINECONE_INDEX_NAME')
        self._create_index()

    def ingest_document(self, filepath):
         #main function
        self.filepath = filepath
        doc = self._load_document()
        chunks = self._create_chunks(doc) 
        str_chunks, metadatas = self._convert_doc_chunks_to_str(chunks)
        embeddings_list = self._create_embeddings_from_chunks(str_chunks)
        vectors_list = self._preparing_ingestions(embeddings_list, str_chunks, metadatas)
        self._store_in_vectordb(vectors_list)
        return 

    def _load_document(self): #load the document
        try:
            self.loader = PyPDFLoader(self.filepath)
            pdf_docs = self.loader.load()
            return pdf_docs
        except Exception:
            raise IngestionError('Unable to load document in ingestion.py _load_document()')

    def _create_chunks(self, document_text):# create the chunks
        try:
            chunks = self.text_splitter.split_documents(document_text)
        # need to only convert page content to string
            return chunks
        except Exception:
            raise IngestionError('Chunking error in ingestion.py _create_chunks()')

    def _convert_doc_chunks_to_str(self, chunks): #convert chunks to string type chunks
        try:
            str_chunks = []
            metadatas = []
            for chunk in chunks:
                string_chunk = str(chunk.page_content)
                str_chunks.append(string_chunk)
                #adding string chunk in metadata
                chunk.metadata["chunk_text"] = string_chunk
                metadatas.append(chunk.metadata)
    
            return str_chunks, metadatas
        except Exception:
            raise IngestionError('Error in ingestion.py _convert_doc_chunks_to_str()')


    def _create_embeddings_from_chunks(self, text_chunks): # create embeddings out of string chunks
        try:
            embeddings = self.embedding.embed_documents(text_chunks) 
            return embeddings
        except Exception:
            raise IngestionError('Error in creating embeddings, ingestion.py,_create_embeddings_from_chunks()')

    def _create_index(self): #initialize index if not already
        try:
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
        except Exception:
            raise IngestionError('Error in creating index pinecone, ingestion.py _create_index()')

    def _preparing_ingestions(self, embeddings_list, string_chunks, metadatas): #prepare vectors for ingestion
        try:
            length_of_embeddings = len(embeddings_list)
            length_of_chunkslist = len(string_chunks)
            vectors_list = []
            if length_of_chunkslist == length_of_embeddings:
                for i in range(0, length_of_chunkslist):
                    vector = {
                        'id': f'{metadatas[i]["source"]}#chunk: {i}',
                        "values": embeddings_list[i],
                        "metadata": metadatas[i]
                            }
                    vectors_list.append(vector)

            return vectors_list
        except Exception:
            raise IngestionError(f'Error in ingestion.py _preparing_ingestions()')

        
    def _store_in_vectordb(self, vectors_list): #upsert in pinecone vector store
        try:
            batch_size = 100
            index = self.pc.Index(host=os.environ.get('INDEX_URL_PINECONE'))
            for i in range(0, len(vectors_list), batch_size):
                index.upsert(
                    namespace = "test-resume",
                    vectors = vectors_list[i: i+batch_size]
                )
    
            return
        except Exception:
            raise IngestionError('Ingestion.py -> Error in storing in vector store, _store_in_vectordb()')
# need to add error handling