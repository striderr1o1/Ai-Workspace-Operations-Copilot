import sys, os 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..")) 
from .agent_config import get_chat_completion, get_chat_completion_system_prompt 
from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents 
from typing import Annotated
from .state import orchestrator_output, graph_state
from .graph import setup_graph

class agentic_workflow:
    def __init__(self, llm_client, kb_agent, bk_agent):
        self.kb_agent = kb_agent
        self.bk_agent = bk_agent
        self.llm_client = llm_client
        self.available_tools = [self.knowledge_base_agent, self.booking_agent]
        self.compiled_graph = setup_graph(self.orchestrator, self.knowledge_base_agent, self.booking_agent, self.tool_call_node)
        return
    
    def get_graph(self):
        return self.compiled_graph

    def orchestrator(self, state: graph_state) -> graph_state:
        try:
            state["tool_calls"].clear()
            system_promptt = get_chat_completion_system_prompt(self.available_tools)
            response = get_chat_completion(llm_client=self.llm_client, state=state, model="openai/gpt-oss-120b:free", response_model=orchestrator_output, system_prompt = system_promptt)
            json_response = response.model_dump()
            if json_response["return_to_user"] == True:
                state["return_to_user_decision"] = True
            state["messages"].append({"role": "assistant", "content": f"""Reasoning: {json_response['reasoning']}...
            _                         ..agent/tool calls: {json_response['tool_calls']}...return to user decision: {json_response["return_to_user"]}"""})
            state["tool_calls"] = json_response["tool_calls"]
            state["return_to_user_decision"] =json_response["return_to_user"]
            state["response_to_user"] = json_response["summary_of_agents_response"] 
            state["count"]+=1
            if state["count"] > 3:
                state["return_to_user_decision"] = True
            return state
        except Exception as e:
            state["return_to_user_decision"] = True
            state["response_to_user"] = f"An Unexpected Error Occured: {e}"
            return state

    def tool_call_node(self, state: graph_state):
        try:
            if state["return_to_user_decision"] == True:
                return "end"
            if len(state["tool_calls"]) != 0:
                toolcall = state["tool_calls"][0]
                if toolcall["tool"] == "knowledge_base_agent":
                    return "knowledge_base_agent"
                if toolcall["tool"] == "booking_agent":
                    return "booking_agent"
            return "orchestrator"
        except Exception as e:
            state["return_to_user_decision"] = True
            state["response_to_user"] = f"An Unexpected Error Occured: {e}"
            return "end"
   
    def knowledge_base_agent(self, state: graph_state)-> graph_state:
        query =""
        toolcall = state["tool_calls"][0]
        if toolcall["tool"] == "knowledge_base_agent":
            query = toolcall["argument"][0]
            state["tool_calls"].remove(toolcall) 
        response = self.kb_agent.invoke({"messages": [{"role": "user", "content": f"Hi, heres your task from orchestrator: {query}"}]})
        summary = response["messages"][-1].content
        state["knowledge_base_agent_output"] = summary
        return state

    def booking_agent(self, state: graph_state)-> graph_state:
        query =""
        if len(state["tool_calls"]) != 0:
            toolcall = state["tool_calls"][0]
            if toolcall["tool"] == "booking_agent":
                query = toolcall["argument"][0]
                state["tool_calls"].remove(toolcall) 
        response = self.bk_agent.invoke({"messages": [{"role": "user", "content": f"Hi, heres your task from orchestrator: {query}"}]})
        state["booking_agent_output"] = response["messages"][-1].content
        return state

