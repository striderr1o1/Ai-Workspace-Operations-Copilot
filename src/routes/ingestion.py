from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from KnowledgeBaseTool.kb_tools import ingest_documents
import tempfile
import os
import shutil
from pydantic import BaseModel
router = APIRouter()


@router.post("/ingestion")
async def ingest_pdf(file: UploadFile = File(...), namespace_name: str = Form(...)):
    tmp_dir = tempfile.mkdtemp()
    try:
        tmp_path = os.path.join(tmp_dir, file.filename)
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        response = ingest_documents([tmp_path], namespace_name)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")
    finally:
        shutil.rmtree(tmp_dir)
