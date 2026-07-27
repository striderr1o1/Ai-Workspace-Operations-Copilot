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
def load_dataset():
    with open(DATASET_PATH, "r") as f:
        return json.load(f)


def load_scenarios(category: str):
    dataset = load_dataset()
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
    return evaluation_status, results

def run_after_agent_response(scenarios):
    """Grade a mid-run decision: a sub agent has already answered, so the
    orchestrator either returns to the user or queues more agent calls.
    Shared by the booking and knowledge base categories, which differ only
    in which agent output the scenario state carries."""
    results = []
    evaluation_status = []
    for s in scenarios:
        print(s["id"])
        condition = False
        state = s["state"]
        output = agent.orchestrator(state)
        results.append(output)
        tools_called_by_agent = output.get("tool_calls") or []
        return_decision_by_agent = output.get("return_to_user_decision")
        if len(tools_called_by_agent)== 0 and return_decision_by_agent == True:
            condition = True
        if len(tools_called_by_agent) > 0 and return_decision_by_agent == False:
            toolcallnames = []
            for tool_call in tools_called_by_agent:
                toolname = tool_call["tool"]
                toolcallnames.append(toolname)
            total_decisions = s["expected"]["decisions"]
            for decision in total_decisions:
                if set(decision["tool_calls"]) == set(toolcallnames):
                    condition = True
        evaluation_status.append(condition)
    return evaluation_status, results

def run_after_booking_response(scenarios):
    return run_after_agent_response(scenarios)

def run_after_kb_response(scenarios):
    return run_after_agent_response(scenarios)

def run_empty_agent_response(scenarios):
    """Grade the decision after a sub agent was called and came back empty:
    retry the agent once, or stop and tell the user honestly. Both the tool
    calls and the return decision are asserted here, because a wrong pairing
    (retrying while claiming to return, or stalling with no call queued) is
    the failure this category exists to catch."""
    results = []
    evaluation_status = []
    for s in scenarios:
        print(s["id"])
        condition = False
        state = s["state"]
        output = agent.orchestrator(state)
        results.append(output)
        if "tool_calls" not in output:
            # orchestrator swallows exceptions into a dict with no tool_calls
            # and return_to_user_decision=True, which is indistinguishable from
            # a correct "give up gracefully" decision. Never score it as a pass.
            print(f"    error: {output.get('response_to_user')}")
            evaluation_status.append(condition)
            continue
        toolcallnames = [toolcall["tool"] for toolcall in output["tool_calls"] or [] if toolcall.get("tool")]
        return_decision_by_agent = output.get("return_to_user_decision")
        for decision in s["expected"]["decisions"]:
            if set(decision["tool_calls"]) == set(toolcallnames) and decision["return_to_user_decision"] == return_decision_by_agent:
                condition = True
                break
        evaluation_status.append(condition)
    return evaluation_status, results

def run_irrelevant(scenarios):
    """Grade greetings and out-of-scope asks, which no sub agent can serve, so
    the orchestrator must answer them itself. Tool calls are not compared: the
    dataset treats return_to_user_decision=true as ignoring them, matching
    tool_call_node, which ends the graph before it reads tool_calls. What is
    checked instead is that response_to_user is non-empty, since here the
    orchestrator's own reply is the entire answer the user receives."""
    results = []
    evaluation_status = []
    for s in scenarios:
        print(s["id"])
        condition = False
        state = s["state"]
        output = agent.orchestrator(state)
        results.append(output)
        if "tool_calls" not in output:
            print(f"    error: {output.get('response_to_user')}")
            evaluation_status.append(condition)
            continue
        return_decision_by_agent = output.get("return_to_user_decision")
        response_to_user = output.get("response_to_user") or ""
        for decision in s["expected"]["decisions"]:
            if decision["return_to_user_decision"] == return_decision_by_agent:
                condition = True
                break
        if condition == True and response_to_user.strip() == "":
            print("    returned to the user with an empty response_to_user")
            condition = False
        evaluation_status.append(condition)
    return evaluation_status, results


