import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Annotated
# initialize graph
# nodes - CRUD operations
# state:
# messages
# tools available
# tool call name 

# this one needs to be implemented
# orchestrator 
# output in json -> tool call: true/false, tool name, reasoning
# conditional node -> get true -> tool node, execute tool calls one by one -> set tool calls
#
class kb_agent_state(TypedDict):
    messages: list
    retrieve_decision: bool
    retrieval_results: str
    retrieval_query: str
class knowledge_base_agent:

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.graph = StateGraph(kb_agent_state)
        self.graph.add_node("orchestrator", self.orchestrator_node)
        self.graph.add_node("retrieval", self.retrieval_node)
        self.graph.add_edge(START, "orchestrator")
        self.graph.add_conditional_edges("orchestrator", self.decision,
                                         {
                                            "retrieve": "retrieval",
                                            "end": END
                                         })
        self.graph.add_edge("retrieval", "orchestrator")
        return

    def get_agent_graph(self):
        return self.graph

    def orchestrator_node(self, state: kb_agent_state):
        system_prompt = """"""
        
        #creating new list with system prompt, passing that to the llm on each iteration
        msg_list = [{"role": "system", "content": system_prompt}] + state["messages"]
        
        #if retrieval was made, add that also
        if state["retrieve_decision"] == True:
            msg_list.append({"role": "user", "content": f"search results: {state['retrieval_results']}"})

        chat_completion = self.llm_client.chat.completions.create(
             messages=msg_list,
             model="openai/gpt-oss-20b:free"
         )
        state["retrieval_query"] = chat_completion.choices[0].message.content
        #adding response to state
        state["messages"].append({"role": "assistant", "content": state["retrieval_query"]})
        print(state["retrieve_decision"])
        return state

    def decision(self, state: kb_agent_state):
        if state["retrieval_query"] == "end":
            state["retrieve_decision"] = False
            return "end"
        state["retrieve_decision"] = True
        return "retrieve"
        
    def retrieval_node(self, state: kb_agent_state):
        state["retrieval_results"] = retrieve_documents(state["retrieval_query"])
        return state



