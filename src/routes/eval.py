import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException

# evaluation_engine lives in evals/ at the repo root, outside src/
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from evals.evaluation_engine import load_scenarios, run_initial_routing, run_after_booking_response, run_after_kb_response, run_empty_agent_response, run_irrelevant

router = APIRouter(prefix="/eval")


@router.post("/initial-routing")
async def eval_initial_routing():
    try:
        scenarios = load_scenarios("initial_routing")
        results, eval_status = run_initial_routing(scenarios)
        return results, eval_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.post("/after-booking-response")
async def eval_after_booking_response():
    try:
        scenarios = load_scenarios("after_booking_response")
        evaluation_status, result = run_after_booking_response(scenarios)
        return evaluation_status, result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.post("/after-kb-response")
async def eval_after_kb_response():
    try:
        scenarios = load_scenarios("after_kb_response")
        evaluation_status, result = run_after_kb_response(scenarios)
        return evaluation_status, result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.post("/empty-agent-response")
async def eval_empty_agent_response():
    try:
        scenarios = load_scenarios("empty_agent_response")
        evaluation_status, result = run_empty_agent_response(scenarios)
        return evaluation_status, result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


@router.post("/irrelevant")
async def eval_irrelevant():
    try:
        scenarios = load_scenarios("irrelevant")
        evaluation_status, result = run_irrelevant(scenarios)
        return evaluation_status, result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")
