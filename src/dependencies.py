# from groq import Groq
from agents.agent_config import get_kb_agent, get_booking_agent, get_orchestrator_client, get_mcp_tools
import json
from agents.agent import agentic_workflow
import asyncio
# 
# def initialize_llm():
#     client = Groq()
#     return client
tools = asyncio.run(get_mcp_tools())
client = get_orchestrator_client()
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
       "response_to_user": "",
       "count": 0
    })
    
    return result

async def run_inference_with_stream(query: str):
    async for chunk in graph.astream(
        {
            "messages": [{"role": "user", "content": query}],
            "tool_calls": [],
            "knowledge_base_agent_output": "",
            "booking_agent_output": "",
            "return_to_user_decision": False,
            "response_to_user": "",
            "count": 0
        },
        stream_mode="updates"
    ):
        for node_name, update in chunk.items():
            print(node_name)
            if node_name=="orchestrator":
                yield f"data: {json.dumps({'event': 'agent calls', 'node': node_name, 'data': update['tool_calls']})}\n\n"
            if node_name=="knowledge_base_agent":
                yield f"data: {json.dumps({'event': 'knowledge base agent', 'data': update['knowledge_base_agent_output']})}\n\n"
            if node_name=="booking_agent":
                yield f"data: {json.dumps({'event': 'booking agent', 'data': update['booking_agent_output']})}\n\n"
            if update["return_to_user_decision"] == True and update.get("response_to_user"):
                yield f"data: {json.dumps({'event': 'final response', 'data': update['response_to_user']})}\n\n"
