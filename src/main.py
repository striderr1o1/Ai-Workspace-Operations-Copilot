from fastapi import FastAPI
from agents.KBagent import knowledge_base_agent
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
#agent = knowledge_base_agent(llm_client=client)
#graph = agent.get_agent_graph().compile()

@app.post("/query")
async def query_agent(request: str):
   # initial_state = {
   #     "messages": [{"role": "user", "content": request}],
   #     "retrieve_decision": False,
   #     "retrieval_results": "",
   #     "retrieval_query": ""
   # }
   # result = graph.invoke(initial_state)
    return result

# left knowledge_base_agent for the while, need to complete supabase crud, then add it to tools, then build its agent or the kb agent
