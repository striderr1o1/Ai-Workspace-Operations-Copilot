from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from dependencies import run_inference, run_inference_with_stream
from services.auth_logic import check_session_exists
from pydantic import BaseModel


router = APIRouter()

class inference(BaseModel):
    query: str

@router.post("/query")
async def query_agent(inf: inference, user: dict = Depends(check_session_exists)):
    try:
        result = run_inference(inf.query, user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")

@router.post("/query-agent")
async def stream_response(inf: inference, user: dict = Depends(check_session_exists)):
    try:
        return StreamingResponse(run_inference_with_stream(inf.query, user), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")
