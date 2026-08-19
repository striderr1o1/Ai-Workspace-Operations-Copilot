from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from services.auth_logic import check_session_exists
from services.supabase_db_functions import (
    get_url_from_supabase,
    get_published_status_from_supabase,
    set_published_status_in_supabase,
    get_slots_from_supabase,
    get_business_id_from_url_string
)

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

@router.post("/c/query-agent/{url_string}")
async def customer_query(url_string: str, request: Request):
    print(url_string) # maybe create a role in the database "customer"
    client = get_supabase_anon_client()
    business_id = get_business_id_from_url_string(client, url_string)
    print(business_id)
    return {"business_id": business_id}

