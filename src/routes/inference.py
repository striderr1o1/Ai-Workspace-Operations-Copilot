from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dependencies import run_inference, run_inference_with_stream

router = APIRouter()

@router.post("/query")
async def query_agent(request: str):
    try:
        result = run_inference(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")

@router.post("/query-agent")
async def stream_response(query: str):
    try:
        return StreamingResponse(run_inference_with_stream(query), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")
