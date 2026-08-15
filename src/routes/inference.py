from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from dependencies import run_inference, run_inference_with_stream
from services.supabase_client import get_supabase_client_with_token
from services.supabase_db_functions import get_published_status_from_supabase
from services.auth_logic import check_session_exists
from pydantic import BaseModel
from utils.exceptions import BadRequestError


router = APIRouter()

class inference(BaseModel):
    query: str

@router.post("/query")
async def query_agent(inf: inference, user: dict = Depends(check_session_exists)):
    try:
        supabase_client = get_supabase_client_with_token(user["access_token"])
        publish_status = get_published_status_from_supabase(supabase_client, user["id"])
        if publish_status is not True:
            raise BadRequestError("URL not published")
        result = run_inference(inf.query, user, supabase_client)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")

@router.post("/query-agent")
async def stream_response(inf: inference, user: dict = Depends(check_session_exists)):
    try:
        supabase_client = get_supabase_client_with_token(user["access_token"])
        publish_status = get_published_status_from_supabase(supabase_client, user["id"])
        if publish_status is not True:
            raise BadRequestError("URL not published")
        return StreamingResponse(run_inference_with_stream(inf.query, user, supabase_client), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")
