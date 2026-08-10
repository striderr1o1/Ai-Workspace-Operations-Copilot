from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from .state import graph_state
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
import os
from dotenv import load_dotenv

load_dotenv()
# get supabase url
def get_checkpointer():
    DB_URI = os.getenv("DATABASE_URL") # says port 5432 failed, means request goes maybe
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        #checkpointer = checkpointer.__enter__()
        checkpointer.setup()
        return checkpointer


def setup_graph(orchestrator, knowledge_base_agent, booking_agent, tool_call_node):
    #checkpointer = get_checkpointer() 
    graph = StateGraph(graph_state)
    graph.add_node("orchestrator", orchestrator, retry_policy = RetryPolicy(max_attempts=3, initial_interval=5.0, backoff_factor=2.0))
    graph.add_node("knowledge_base_agent", knowledge_base_agent, retry_policy = RetryPolicy(max_attempts=3, initial_interval=5.0, backoff_factor=2.0))
    graph.add_node("booking_agent", booking_agent, retry_policy = RetryPolicy(max_attempts=3, initial_interval=5.0, backoff_factor=2.0))
    graph.add_edge(START, "orchestrator")
    graph.add_conditional_edges("orchestrator", tool_call_node,
                                 {
                                    "end": END,
                                    "knowledge_base_agent": "knowledge_base_agent",
                                    "booking_agent": "booking_agent",
                                    "orchestrator": "orchestrator"
                                 })
    graph.add_conditional_edges("knowledge_base_agent", tool_call_node,
                                 {
                                    "end": END,
                                    "knowledge_base_agent": "knowledge_base_agent",
                                    "booking_agent": "booking_agent",
                                    "orchestrator": "orchestrator"
                                 })
    graph.add_conditional_edges("booking_agent", tool_call_node,
                                 {
                                    "end": END,
                                    "knowledge_base_agent": "knowledge_base_agent",
                                    "booking_agent": "booking_agent",
                                    "orchestrator": "orchestrator"
                                 })
    return graph
