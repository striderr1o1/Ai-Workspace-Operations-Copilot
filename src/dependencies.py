# from groq import Groq
from agents.agent_config import get_kb_agent, get_booking_agent, get_subagents_client
import json
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

async def run_inference_with_stream(query: str):
    async for chunk in graph.astream(
        {
            "messages": [{"role": "user", "content": query}],
            "tool_calls": [],
            "knowledge_base_agent_output": "",
            "booking_agent_output": "",
            "return_to_user_decision": False,
        },
        stream_mode="updates"
    ):
        for node_name, update in chunk.items():
            if update.get("tool_calls"):
                yield f"data: {json.dumps({'event': 'tool_calls', 'node': node_name, 'data': update['tool_calls']})}\n\n"
            if update.get("knowledge_base_agent_output"):
                yield f"data: {json.dumps({'event': 'kb_result', 'data': update['knowledge_base_agent_output']})}\n\n"
            if update.get("booking_agent_output"):
                yield f"data: {json.dumps({'event': 'booking_result', 'data': update['booking_agent_output']})}\n\n"
            if update.get("return_to_user_decision") and update.get("response_to_user"):
                yield f"data: {json.dumps({'event': 'final', 'data': update['response_to_user']})}\n\n"
