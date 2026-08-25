import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from services.auth_logic import check_session_exists

# evaluation_engine lives in evals/ at the repo root, outside src/
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from evals.evaluation_engine import load_dataset, load_scenarios, run_initial_routing, run_after_booking_response, run_after_kb_response, run_empty_agent_response, run_irrelevant

router = APIRouter(prefix="/eval")


def build_report(category: str, scenarios, evaluation_status, results):
    """Fold a grader's parallel output lists back into one row per scenario.

    Every grader returns (evaluation_status, results) positionally aligned with
    the scenarios it was handed, but each category asserts something different.
    The frontend should not have to know which; it renders correctness against
    expected and actual for all five the same way, so the shaping happens here.
    """
    cases = []
    for scenario, correct, actual in zip(scenarios, evaluation_status, results):
        cases.append({
            "id": scenario["id"],
            "correct": bool(correct),
            "query": next(
                (m["content"] for m in reversed(scenario["state"].get("messages") or []) if m.get("role") == "user"),
                "",
            ),
            "expected": scenario["expected"],
            "actual": actual,
        })
    passed = sum(1 for c in cases if c["correct"])
    return {
        "category": category,
        "total": len(cases),
        "passed": passed,
        "failed": len(cases) - passed,
        "cases": cases,
    }


def run_category(category: str, runner, user: dict):
    try:
        scenarios = load_scenarios(category)
        evaluation_status, results = runner(scenarios, user)
        return build_report(category, scenarios, evaluation_status, results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")


#@router.get("/dataset")
#async def eval_dataset(user: dict = Depends(check_session_exists)):
#    """Serve the scenario dataset so the frontend can show what it is about to
#    run before running it."""
#    try:
#        dataset = load_dataset()
#        counts = {}
#        for scenario in dataset["scenarios"]:
#            category = scenario.get("category")
#            counts[category] = counts.get(category, 0) + 1
#        return {
#            "name": dataset.get("name"),
#            "layer": dataset.get("layer"),
#            "version": dataset.get("version"),
#            "description": dataset.get("description"),
#            "categories": [
#                {"category": category, "endpoint": category.replace("_", "-"), "count": count}
#                for category, count in counts.items()
#            ],
#            "scenarios": dataset["scenarios"],
#        }
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")
#
#
#@router.post("/initial-routing")
#async def eval_initial_routing(user: dict = Depends(check_session_exists)):
#    return run_category("initial_routing", run_initial_routing, user)
#
#
#@router.post("/after-booking-response")
#async def eval_after_booking_response(user: dict = Depends(check_session_exists)):
#    return run_category("after_booking_response", run_after_booking_response, user)
#
#
#@router.post("/after-kb-response")
#async def eval_after_kb_response(user: dict = Depends(check_session_exists)):
#    return run_category("after_kb_response", run_after_kb_response, user)
#
#
#@router.post("/empty-agent-response")
#async def eval_empty_agent_response(user: dict = Depends(check_session_exists)):
#    return run_category("empty_agent_response", run_empty_agent_response, user)
#
#
#@router.post("/irrelevant")
#async def eval_irrelevant(user: dict = Depends(check_session_exists)):
#    return run_category("irrelevant", run_irrelevant, user)
