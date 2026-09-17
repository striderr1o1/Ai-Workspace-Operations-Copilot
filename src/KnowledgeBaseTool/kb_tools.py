from .ingestion import Ingestion
from .retrieval import Retrieval
from services.supabase_db_functions import get_namespacename_from_supabase
from langchain.tools import tool
from langchain_core.tools import ToolException
from langchain_core.runnables import RunnableConfig
from pinecone import AsyncPinecone
import os
async def ingest_documents(documents_list, namespace, supabase_client=None, user_id=None):
    """Ingestion documents in this function as a list when
    you get a list of documents to ingest"""
    try:
        ingestion_obj = Ingestion(supabase_client, user_id)
        for doc_path in documents_list:
            await ingestion_obj.ingest_document(doc_path, namespace)
        return
    except Exception as e:
        raise ToolException(f"Error in using tool: {e}")

@tool
async def retrieve_documents(query, config: RunnableConfig):
    """retrieve relevant documents by putting the query in
    this function, use one namespace at a time """
    try:
        user_id = config["configurable"]["user_id"]
        supabase_client = config["configurable"]["supabase_client"]
        namespace_name = await get_namespacename_from_supabase(supabase_client, user_id)
        retrieval_obj = Retrieval()
        results = await retrieval_obj.retrieve(query, namespace_name)
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

async def create_namespace_from_name(namespacename):
    async with AsyncPinecone(api_key=os.environ.get('PINECONE_API_KEY')) as pc:
        index = await pc.index(host=os.environ.get('INDEX_URL_PINECONE'))
        # the index client holds its own connection pool - closing pc does not
        # close it, so it needs its own `async with`
        async with index:
            ns = await index.create_namespace(
                name=namespacename,
              )
    return
