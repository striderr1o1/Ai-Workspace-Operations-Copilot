from fastapi import FastAPI
from agents.agent import agentic_workflow
from agents.agent_config import get_kb_agent, get_booking_agent, get_subagents_client

app = FastAPI()

client = get_subagents_client()
kb_agent = get_kb_agent()
booking_agent = get_booking_agent()
agent = agentic_workflow(llm_client=client, kb_agent=kb_agent, bk_agent=booking_agent)
graph = agent.get_graph()

@app.post("/query")
async def query_agent(request: str):
    result = graph.invoke({
        "messages": [{"role": "user", "content": request}],
        "tool_calls": [],
        "knowledge_base_agent_output": "",
        "booking_agent_output": "",
        "finance_agent_output": "",
        "return_to_user_decision": False,
    })
    return result

# left knowledge_base_agent for the while, need to complete supabase crud, then add it to tools, then build its agent or the kb agent
