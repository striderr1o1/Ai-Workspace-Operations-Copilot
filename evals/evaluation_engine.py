import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# code imports are relative to src/ and .env lives at repo root,
# so bootstrap both before importing app code
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
load_dotenv(REPO_ROOT / ".env")

from agents.agent_config import get_kb_agent, get_booking_agent, get_orchestrator_client
from agents.agent import agentic_workflow
from agents.graph import setup_graph

DATASET_PATH = REPO_ROOT / "evals" / "orchestrator_dataset.json"

client = get_orchestrator_client()
kb_agent = get_kb_agent()
booking_agent = get_booking_agent()
agent = agentic_workflow(llm_client=client, kb_agent=kb_agent, bk_agent=booking_agent, setup_graph=setup_graph)

def load_scenarios(category: str):
    with open(DATASET_PATH, "r") as f:
        dataset = json.load(f)
    return [s for s in dataset["scenarios"] if s.get("category") == category]


def run_initial_routing(scenarios):
    results = []
    evaluation_status = []
    for s in scenarios:
        print(s["id"])
        tool_calls_same = False
        state = s["state"]
        output = agent.orchestrator(state)
        results.append(output)
        tools_called = [toolcall["tool"] for toolcall in output.get("tool_calls") or [] if toolcall.get("tool")]
        total_decisions = s["expected"]["decisions"]
        for decision in total_decisions:
            toolcalls = decision["tool_calls"]
            if set(toolcalls) == set(tools_called):
                tool_calls_same = True
                break
        evaluation_status.append(tool_calls_same) 
    return results, evaluation_status




