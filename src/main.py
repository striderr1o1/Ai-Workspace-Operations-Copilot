from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from KnowledgeBaseTool.kb_tools import ingest_documents
from typing import List
import tempfile
import os
import shutil
from dependencies import run_inference, run_inference_with_stream
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/query")
async def query_agent(request: str):
    try:
        result = run_inference(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}");

@app.post("/ingestion")
async def ingest_pdf(file: UploadFile, namespace_name: str):
    tmp_dir = tempfile.mkdtemp() #creating temp dir
    try:
        tmp_path = os.path.join(tmp_dir, file.filename) #creating file path
        with open(tmp_path, "wb") as f: # writing to that file
            shutil.copyfileobj(file.file, f)
        response = ingest_documents([tmp_path], namespace_name)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}");
    finally:
        # removes temp dir
        shutil.rmtree(tmp_dir)

@app.post("/query-agent")
async def stream_response(query: str):
    try: 
        return StreamingResponse(run_inference_with_stream(query), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}");
