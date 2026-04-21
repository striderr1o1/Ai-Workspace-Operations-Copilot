from fastapi import FastAPI
from agents.agent import initialize_agent
app = FastAPI()
agent = initialize_agent()

@app.post("/query")
async def query_agent(request: str):
    result = agent.invoke({"messages": [{"role": "user", "content": f"{request}"}]})
    return result