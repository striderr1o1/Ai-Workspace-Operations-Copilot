from pyexpat.errors import messages
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Annotated
from pydantic import BaseModel

class graph_state(TypedDict):
    messages: list
    tool_calls: list 
    knowledge_base_agent_output: str
    booking_agent_output: str
    finance_agent_output: str

class orchestrator_output(BaseModel):
    reasoning: str
    tool_calls: list #for agent calls
class agentic_workflow:

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.available_tools = [self.knowledge_base_agent]
        self.graph = StateGraph(graph_state)
        self.graph.add_node("orchestrator", self.orchestrator)
        self.graph.add_node("knowledge_base_agent", self.knowledge_base_agent)
        self.graph.add_edge(START, "orchestrator")
        self.graph.add_conditional_edges("orchestrator", self.tool_call_node,
                                         {
                                            "knowledge_base_agent":"knowledge_base_agent"
                                         })
        self.compiled_graph = self.graph.compile()
        return
    
    def get_graph(self):
        return self.compiled_graph

    def orchestrator(self, state: graph_state) -> graph_state:
        system_prompt = f"""You are an orchestrator agent.
                You have access to the following agents:
                {self.available_tools}
                ...
                You will call agents based on user requirement and deliver the answer.
                Avoid excessive question, do as youre told. Give response in the following
                json format: 
                reasoning: str, tool_calls: list  -> this must be in json format. Dont add
                any other character or symbol... dont add backticks``, use the json brackets 
                instead...
                use this json format:
                {{
                    "reasoning": "...",
                    "tool_calls": {{
                        "tool": ...,
                        "argument":[]

                    }}
                }}
                """
        response = self.llm_client.chat.completions.create(
                
            model="openai/gpt-oss-120b:free",
            messages=[{"role": "system", "content": system_prompt}] + state["messages"],
            response_model=orchestrator_output,
        )
        print(response)
        return state

    def tool_call_node(self, state: graph_state):
        return "knowledge_base_agent"
   
    def knowledge_base_agent(self, state: graph_state)-> graph_state:
        return state
# orchestrator
# knowledge base agent
