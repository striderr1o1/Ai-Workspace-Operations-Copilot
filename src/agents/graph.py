from langgraph.graph import StateGraph, START, END
from .state import graph_state


def setup_graph(orchestrator, knowledge_base_agent, booking_agent, tool_call_node):
    graph = StateGraph(graph_state)
    graph.add_node("orchestrator", orchestrator)
    graph.add_node("knowledge_base_agent", knowledge_base_agent)
    graph.add_node("booking_agent", booking_agent)
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
    return graph.compile()
