from fastapi import FastAPI
from agents.KBagent import knowledge_base_agent
from groq import Groq
import os
app = FastAPI()
client = Groq()
agent = knowledge_base_agent(llm_client=client)
graph = agent.get_agent_graph().compile()

@app.post("/query")
async def query_agent(request: str):
    initial_state = {
        "messages": [{"role": "user", "content": request}],
        "retrieve_decision": False,
        "retrieval_results": "",
        "retrieval_query": ""
    }
    result = graph.invoke(initial_state)
    return result
