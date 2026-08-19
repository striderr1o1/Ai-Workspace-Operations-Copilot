from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from dependencies import run_inference, run_inference_with_stream
from services.supabase_client import get_supabase_client_with_token
from services.auth_logic import check_session_exists
from pydantic import BaseModel


router = APIRouter()

class inference(BaseModel):
    query: str

@router.post("/query")
async def query_agent(inf: inference, user: dict = Depends(check_session_exists)):
    try:
        supabase_client = get_supabase_client_with_token(user["access_token"])
        result = run_inference(inf.query, user, supabase_client)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")

@router.post("/query-agent")
async def stream_response(inf: inference, user: dict = Depends(check_session_exists)):
    try:
        supabase_client = get_supabase_client_with_token(user["access_token"])
        return StreamingResponse(run_inference_with_stream(inf.query, user, supabase_client), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")
