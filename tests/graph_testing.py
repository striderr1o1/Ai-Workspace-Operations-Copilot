import sys
import operator
from typing import Annotated
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from agents.state import graph_state, orchestrator_output
from agents.graph import setup_graph
from unittest.mock import Mock

def test_setup_graph():
    orchestrator = Mock()
    booking_agent = Mock()
    knowledge_base_agent = Mock()
    toolcallnode = Mock()

    orchestrator.return_value = Mock(
        messages = Annotated[list, operator.add],
        tool_calls = list,
        knowledge_base_agent_output = str,
        booking_agent_output = str,
        return_to_user_decision = bool,
        response_to_user = str,
        count = int
            )
    
    toolcallnode.return_value = "knowledge_base_agent"

    booking_agent.return_value = Mock(
        messages = Annotated[list, operator.add],
        tool_calls = list,
        knowledge_base_agent_output = str,
        booking_agent_output = str,
        return_to_user_decision = bool,
        response_to_user = str,
        count = int
            )
    knowledge_base_agent.return_value = Mock(
        messages = Annotated[list, operator.add],
        tool_calls = list, 
        knowledge_base_agent_output = str,
        booking_agent_output = str,
        return_to_user_decision = bool,
        response_to_user = str,
        count = int
            )
    graph = setup_graph(orchestrator, knowledge_base_agent, booking_agent, toolcallnode)

    assert graph is not None
    
