import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException

# evaluation_engine lives in evals/ at the repo root, outside src/
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from evals.evaluation_engine import load_scenarios

router = APIRouter(prefix="/eval")


@router.post("/initial-routing")
async def eval_initial_routing():
    try:
        return load_scenarios("initial_routing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.post("/after-booking-response")
async def eval_after_booking_response():
    try:
        return load_scenarios("after_booking_response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.post("/after-kb-response")
async def eval_after_kb_response():
    try:
        return load_scenarios("after_kb_response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.post("/empty-agent-response")
async def eval_empty_agent_response():
    try:
        return load_scenarios("empty_agent_response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.post("/irrelevant")
async def eval_irrelevant():
    try:
        return load_scenarios("irrelevant")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")
