from .ingestion import Ingestion
from .retrieval import Retrieval
from services.supabase_db_functions import get_namespacename_from_supabase
from langchain.tools import tool
from langchain_core.tools import ToolException
from langchain_core.runnables import RunnableConfig
from pinecone import Pinecone
import os
def ingest_documents(documents_list, namespace, supabase_client=None, user_id=None):
    """Ingestion documents in this function as a list when
    you get a list of documents to ingest"""
    try:
        ingestion_obj = Ingestion(supabase_client, user_id)
        for doc_path in documents_list:
            ingestion_obj.ingest_document(doc_path, namespace)
        return
    except Exception as e:
        raise ToolException(f"Error in using tool: {e}")

@tool    
def retrieve_documents(query, config: RunnableConfig):
    """retrieve relevant documents by putting the query in
    this function, use one namespace at a time """
    try:
        user_id = config["configurable"]["user_id"]
        supabase_client = config["configurable"]["supabase_client"]
        namespace_name = get_namespacename_from_supabase(supabase_client, user_id)
        retrieval_obj = Retrieval()
        results =retrieval_obj.retrieve(query, namespace_name)
        return results
    except Exception as e:
        raise ToolException(f"Error in using tool: {e}")


#@tool
#def get_all_namespaces():
#    """use this function to get namespaces names"""
#    pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
#    index = pc.Index(host=os.environ.get('INDEX_URL_PINECONE'))
#    stats = index.describe_index_stats()
#    namespaces = list(stats.namespaces.keys())
#    return namespaces

def create_namespace_from_name(namespacename):
    pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
    index = pc.Index(host=os.environ.get('INDEX_URL_PINECONE'))
    ns = index.create_namespace(
        name=namespacename,
      )
    return

def return_record_count(namespacename):
    pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
    index = pc.Index(host=os.environ.get('INDEX_URL_PINECONE'))
    stats = index.describe_index_stats()
    namespace_stats = stats.namespaces.get(namespacename)
    count = namespace_stats.vector_count if namespace_stats else 0
    record_names = []
    for ids in index.list(namespace=namespacename):
        record_names.extend(ids)
    return {"count": count, "record_names": record_names}
