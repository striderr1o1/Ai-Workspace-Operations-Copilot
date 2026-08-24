from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dependencies import run_inference_with_stream
from services.auth_logic import check_session_exists
from utils.exceptions import BadRequestError
from services.supabase_db_functions import (
    get_url_from_supabase,
    get_published_status_from_supabase,
    set_published_status_in_supabase,
    get_slots_from_supabase,
    get_business_id_from_url_string,
    get_namespacename_from_supabase,
    confirm_booking_by_verification_id
)
from KnowledgeBaseTool.kb_tools import return_record_count

from services.supabase_client import get_supabase_client_with_token, get_supabase_anon_client
router = APIRouter()


@router.get("/get-url")
async def get_url(user: dict = Depends(check_session_exists)):
    try:
        user_id = user["id"]
        access_token = user["access_token"]
        supabase_client = get_supabase_client_with_token(access_token)
        url = get_url_from_supabase(supabase_client, user_id)
        published = get_published_status_from_supabase(supabase_client, user_id)
        return {
                "url": url,
                "published": published
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


class PublishStatus(BaseModel):
    published: bool


class QueryRequest(BaseModel):
    query: str


@router.post("/set-publish")
async def set_publish(status: PublishStatus, user: dict = Depends(check_session_exists)):
    try:
        user_id = user["id"]
        access_token = user["access_token"]
        supabase_client = get_supabase_client_with_token(access_token)
        published = set_published_status_in_supabase(supabase_client, user_id, status.published)
        return {"published": published}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.get("/get-slots-data")
async def get_slots_data(user: dict = Depends(check_session_exists)):
    try:
        user_id = user["id"]
        access_token = user["access_token"]
        supabase_client = get_supabase_client_with_token(access_token)
        slots = get_slots_from_supabase(supabase_client, user_id)
        return {"slots": slots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")

@router.get("/get-record-count")
async def get_record_count(user: dict = Depends(check_session_exists)):
    try:
        user_id = user["id"]
        access_token = user["access_token"]
        supabase_client = get_supabase_client_with_token(access_token)
        namespace_name = get_namespacename_from_supabase(supabase_client, user_id)
        result = return_record_count(namespace_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.post("/c/query-agent/{url_string}")
async def customer_query(url_string: str, inf: QueryRequest):
    try:
        client = get_supabase_anon_client()
        business_id = get_business_id_from_url_string(client, url_string)
        publish_status = get_published_status_from_supabase(client, business_id)
        if publish_status is not True:
            raise BadRequestError("URL not published")
        user = {"id": business_id}
        return StreamingResponse(
            run_inference_with_stream(inf.query, user, client),
            media_type="text/event-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.get("/booking-confirmation/{verification_id}")
async def booking_confirmation(verification_id: str):
    try:
        client = get_supabase_anon_client()
        confirm_booking_by_verification_id(client, verification_id)
        return {"message": "Booking confirmed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")

