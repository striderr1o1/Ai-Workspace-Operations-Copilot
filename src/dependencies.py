import uuid
from agents.agent_config import get_kb_agent, get_booking_agent, get_orchestrator_client
from services.supabase_client import get_supabase_client_with_token
import json
from agents.agent import agentic_workflow
from agents.graph import setup_graph


def run_inference(query: str, user: dict, thread_id: str = "thread-1"):
    user_id = user["id"]
    access_token = user["access_token"]
    client = get_orchestrator_client()
    # per-request supabase client, authenticated as this user so RLS sees their auth.uid()
    supabase_client = get_supabase_client_with_token(access_token)
    kb_agent = get_kb_agent(user_id, supabase_client)
    booking_agent = get_booking_agent(user_id, supabase_client)
    agent = agentic_workflow(llm_client=client, kb_agent=kb_agent, bk_agent=booking_agent, setup_graph=setup_graph)
    graph = agent.get_graph()

    result = graph.invoke({
       "messages": [{"role": "user", "content": query}],
       "tool_calls": [],
       "knowledge_base_agent_output": "",
       "booking_agent_output": "",
       "return_to_user_decision": False,
       "response_to_user": "",
       "count": 0
    },
    {"configurable": {"thread_id": thread_id}},
                          )

    return result

async def run_inference_with_stream(query: str, user: dict, thread_id: str = "thread-1"):
    user_id = user["id"]
    access_token = user["access_token"]
    client = get_orchestrator_client()
    # per-request supabase client, authenticated as this user so RLS sees their auth.uid()
    supabase_client = get_supabase_client_with_token(access_token)
    kb_agent = get_kb_agent(user_id, supabase_client)
    booking_agent = get_booking_agent(user_id, supabase_client)
    agent = agentic_workflow(llm_client=client, kb_agent=kb_agent, bk_agent=booking_agent, setup_graph=setup_graph)
    graph = agent.get_graph()

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
    {"configurable": {"thread_id": thread_id}},
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
            if update.get("return_to_user_decision") == True and update.get("response_to_user"):
                yield f"data: {json.dumps({'event': 'final response', 'data': update['response_to_user']})}\n\n"
