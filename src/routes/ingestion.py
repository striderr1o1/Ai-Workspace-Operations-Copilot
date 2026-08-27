from fastapi import APIRouter, UploadFile, HTTPException, Form, File, Depends
from KnowledgeBaseTool.kb_tools import ingest_documents
from services.auth_logic import check_session_exists
from services.supabase_db_functions import get_namespacename_from_supabase
from services.supabase_client import get_supabase_client_with_token
import tempfile
import os
import shutil
from pydantic import BaseModel
router = APIRouter()


@router.post("/ingestion")
async def ingest_pdf(file: UploadFile = File(...), user: dict = Depends(check_session_exists)):
    # the dependency already validated the JWT; resolve this user's namespace
    # the same way retrieve_documents does (scoped to their own business_id)
    supabase_client = get_supabase_client_with_token(user["access_token"])
    namespace_name = get_namespacename_from_supabase(supabase_client, user["id"])
    tmp_dir = tempfile.mkdtemp()
    try:
        tmp_path = os.path.join(tmp_dir, file.filename)
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        response = ingest_documents([tmp_path], namespace_name, supabase_client, user["id"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")
    finally:
        shutil.rmtree(tmp_dir)
