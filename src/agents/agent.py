import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents
from langgraph.graph import StateGraph, START, END
from typing import Annotated
from .state import orchestrator_output, graph_state

class agentic_workflow:

    def __init__(self, llm_client, kb_agent, bk_agent):
        self.kb_agent = kb_agent
        self.bk_agent = bk_agent
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
            messages=[{"role": "system", "content": system_prompt}] + state["messages"] + [{"role": "user", "content": f"""Agent outputs — 
                    knowledge_base_agent: {state['knowledge_base_agent_output']}, booking_agent: {state['booking_agent_output']},
                    finance_agent: {state['finance_agent_output']}"""}],
            response_model=orchestrator_output,
        )
        json_response = response.model_dump()
        # getting llm reasoning from response and pushing it to messages state
        state["messages"].append({"role": "assistant", "content": f"""Reasoning: {json_response['reasoning']}...
                                  ..agent/tool calls: {json_response['tool_calls']}"""})
        #storing tool calls 
        state["tool_calls"] = response.model_dump()["tool_calls"]
        state["return_to_user_decision"] = response.model_dump()["return_to_user"]
        print(json_response)
        return state

    def tool_call_node(self, state: graph_state):
        if state["return_to_user_decision"] == True:
            return "end"
        for toolcall in state["tool_calls"]:
            if toolcall["tool"] == "knowledge_base_agent":
                response = self.knowledge_base_agent(state)
            if toolcall["tool"] == "booking_agent":
                response_b = self.booking_agent(state)


        return "end"
   
    def knowledge_base_agent(self, state: graph_state)-> graph_state:
        query =""
        for toolcall in state["tool_calls"]:
            if toolcall["tool"] == "knowledge_base_agent":
                query = toolcall["argument"]
        
        response = self.kb_agent.invoke({"messages": [{"role": "user", "content": f"Hi, heres your task from orchestrator: {query}"}]})
        state["knowledge_base_agent_output"] = response
#        print(state["knowledge_base_agent_output"]) need to fix this to return just the text including raw chunks and model response
        return state

    def booking_agent(self, state: graph_state)-> graph_state:
        query =""
        for toolcall in state["tool_calls"]:
            if toolcall["tool"] == "booking_agent":
                query = toolcall["argument"]

        response = self.bk_agent.invoke({"messages": [{"role": "user", "content": f"Hi, heres your task from orchestrator: {query}"}]})
        state["booking_agent_output"] = response
        return state

    #need to check how to end the workflow add tool_call_node
