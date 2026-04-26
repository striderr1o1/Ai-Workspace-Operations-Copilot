from langchain_groq import ChatGroq
from langchain.agents import create_agent
from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents
from services.supabase_client import fetch_room_data
llm = ChatGroq(
        model = "qwen/qwen3-32b",
        temperature=0,
        )

def get_kb_agent():
    agent = create_agent(
            model=llm,
            tools = [retrieve_documents],
            )
    return agent

def get_booking_agent():
    agent = create_agent(
            model = llm,
            tools = [fetch_room_data]
            )
    return agent

