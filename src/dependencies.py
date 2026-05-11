# from groq import Groq
from agents.agent_config import get_kb_agent, get_booking_agent, get_subagents_client
from agents.agent import agentic_workflow
# 
# def initialize_llm():
#     client = Groq()
#     return client
client = get_subagents_client()
kb_agent = get_kb_agent()
booking_agent = get_booking_agent()
agent = agentic_workflow(llm_client=client, kb_agent=kb_agent, bk_agent=booking_agent)
graph = agent.get_graph()


def run_inference(query: str):
    result = graph.invoke({
       "messages": [{"role": "user", "content": query}],
       "tool_calls": [],
       "knowledge_base_agent_output": "",
       "booking_agent_output": "",
       "return_to_user_decision": False,
    })
    
    return result
