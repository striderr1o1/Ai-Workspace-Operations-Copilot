from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.auth_logic import check_session_exists
from services.supabase_db_functions import get_url_from_supabase, get_published_status_from_supabase

from services.supabase_client import get_supabase_client_with_token
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
        # TODO: persist status.published on this user's links row
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")

