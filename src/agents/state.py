from pydantic import BaseModel
from typing_extensions import TypedDict

class graph_state(TypedDict):
    messages: list
    tool_calls: list 
    knowledge_base_agent_output: str
    booking_agent_output: str
    finance_agent_output: str
    return_to_user_decision: bool

class orchestrator_output(BaseModel):
    reasoning: str
    tool_calls: list #for agent calls
    return_to_user: bool


