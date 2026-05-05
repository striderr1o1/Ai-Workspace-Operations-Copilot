from fastapi import FastAPI, File, UploadFile
from agents.agent import agentic_workflow
from agents.agent_config import get_kb_agent, get_booking_agent, get_subagents_client
from KnowledgeBaseTool.kb_tools import ingest_documents
from typing import List
import tempfile
import os
import shutil
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
    print('\n\n')
    print(result)
    return result

# left knowledge_base_agent for the while, need to complete supabase crud, then add it to tools, then build its agent or the kb agent

# need to add the MCP server also for finance agent

@app.post("/ingestion")
async def ingest_pdf(file: UploadFile, namespace_name: str):
    tmp_dir = tempfile.mkdtemp() #creating temp dir
    try:
        tmp_path = os.path.join(tmp_dir, file.filename) #creating file path
        with open(tmp_path, "wb") as f: # writing to that file
            shutil.copyfileobj(file.file, f)
        response = ingest_documents([tmp_path], namespace_name)
        return response
    finally:
        # removes temp dir
        shutil.rmtree(tmp_dir)


