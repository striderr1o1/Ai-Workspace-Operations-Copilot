import sys, os
from langchain.agents import create_agent
from openai import Client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from agents.agent import agentic_workflow
from agents.graph import setup_graph
from openai import Client
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from unittest.mock import Mock

def test_agentic_workflow_class():
    orchestrator_client = Mock()
    orchestrator_client.return_value = Client(api_key="fsdfds")
    kb_agent = Mock()
    booking_agent= Mock()
    kb_agent.return_value = create_agent(model = ChatGroq(model = "lol"))
    booking_agent.return_value = create_agent(model = ChatGroq(model = "lol"))

    agent_class = agentic_workflow(orchestrator_client, kb_agent, booking_agent, setup_graph)
    
    assert type(agent_class) == agentic_workflow
    assert agent_class is not None 
    assert agent_class.orchestrator is not None
    assert agent_class.tool_call_node is not None
    assert agent_class.knowledge_base_agent is not None
    assert agent_class.booking_agent is not None
    
