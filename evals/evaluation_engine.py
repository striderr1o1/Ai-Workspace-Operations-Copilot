# import orchestrator and sub agent clients
# push the scenarios in the function, loop them.
# break the workflow part that isnt required.
import sys
from pathlib import Path
from dotenv import load_dotenv

# code imports are relative to src/ and .env lives at repo root,
# so bootstrap both before importing app code
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
load_dotenv(REPO_ROOT / ".env")

from agents.agent_config import get_kb_agent, get_booking_agent, get_orchestrator_client
from agents.agent import agentic_workflow

client = get_orchestrator_client()
kb_agent = get_kb_agent()
booking_agent = get_booking_agent()
agent = agentic_workflow(llm_client=client, kb_agent=kb_agent, bk_agent=booking_agent)
