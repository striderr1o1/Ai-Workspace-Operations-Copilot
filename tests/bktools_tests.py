import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from agents.agent import agentic_workflow
from agents.agent_config import get_kb_agent, get_booking_agent, get_chat_completion_system_prompt, get_chat_completion, get_subagents_client
from agents.state import orchestrator_output, graph_state
from agents.graph import setup_graph
from KnowledgeBaseTool.retrieval import Retrieval
from services.supabase_client import fetch_room_data, update_room_data, insert_room_data

def test_retrieval(query, namespace):
    retrieve_obj = Retrieval()
    response = retrieve_obj.retrieve(query, namespace)
    return response

# print(test_retrieval("Workspace policies", "office_doc"))


