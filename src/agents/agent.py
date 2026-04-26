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
    return_to_user_decision: bool

class orchestrator_output(BaseModel):
    reasoning: str
    content: str
    tool_calls: list #for agent calls
    return_to_user: bool

class agentic_workflow:

    def __init__(self, llm_client, kb_agent, booking_agent):
        self.kb_agent = kb_agent
        self.booking_agent = booking_agent
        self.llm_client = llm_client
        self.available_tools = [self.knowledge_base_agent, self.booking_agent]
        self.graph = StateGraph(graph_state)
        self.graph.add_node("orchestrator", self.orchestrator)
        self.graph.add_node("knowledge_base_agent", self.knowledge_base_agent)
        self.graph.add_edge(START, "orchestrator")
        self.graph.add_conditional_edges("orchestrator", self.tool_call_node,
                                         {
                                            "knowledge_base_agent":"knowledge_base_agent",
                                            "end": END,
                                            "orchestrator": "orchestrator"

                                         })
        self.compiled_graph = self.graph.compile()
        return
    
    def get_graph(self):
        return self.compiled_graph

    def orchestrator(self, state: graph_state) -> graph_state:
        print("call")
        state["tool_calls"].clear()
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
                    "content": "...output to user..."
                    "tool_calls": [{{
                        "tool": ...,
                        "argument":[]

                    }}],
                    "return_to_user": true/false
                }}, you must also include the json curly braces

                do not exceed more than 2 iterations or if the agents/tools have returned
                their results, then just stop and return to user
                """
        response = self.llm_client.chat.completions.create(

            model="openai/gpt-oss-120b:free",
            messages=[{"role": "system", "content": system_prompt}] + state["messages"] + [{"role": "user", "content": f"Agent outputs — knowledge_base_agent: {state['knowledge_base_agent_output']}, booking_agent: {state['booking_agent_output']}, finance_agent: {state['finance_agent_output']}"}],
            response_model=orchestrator_output,
        )
        json_response = response.model_dump()
        print(json_response)
        # getting llm reasoning from response and pushing it to messages state
        state["messages"].append({"role": "assistant", "content": f"Reasoning: {json_response['reasoning']}...Content: {json_response['content']}...agent/tool calls: {json_response['tool_calls']}"})
        #storing tool calls 
        state["tool_calls"] = response.model_dump()["tool_calls"]
        state["return_to_user_decision"] = response.model_dump()["return_to_user"]
        return state

    def tool_call_node(self, state: graph_state):
        if state["return_to_user_decision"] == True:
            return "end"
        for toolcall in state["tool_calls"]:
            if toolcall["tool"] == "knowledge_base_agent":
                response = self.knowledge_base_agent(state)
            if toolcall["tool"] == "booking_agent":
                response_b = self.booking_agent(state)


        return "orchestrator"
   
    def knowledge_base_agent(self, state: graph_state)-> graph_state:
        query =""
        for toolcall in state["tool_calls"]:
            if toolcall["tool"] == "knowledge_base_agent":
                query = toolcall["argument"]
        
        response = self.kb_agent.invoke({"messages": [{"role": "user", "content": f"Hi, heres your task from orchestrator: {query}"}]})
        print(response)
        state["knowledge_base_agent_output"] = response
        return state

    def booking_agent(self, state: graph_state)-> graph_state:
        return state

    #need to check how to end the workflow add tool_call_node
