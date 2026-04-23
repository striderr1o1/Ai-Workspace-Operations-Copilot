import stat
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Annotated
# initialize graph
# nodes - CRUD operations

class kb_agent_state(TypedDict):
    messages: list
    retrieve_decision: bool
    retrieval_results: str
    retrieval_query: str
class knowledge_base_agent:

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.graph = StateGraph(kb_agent_state)
        self.graph.add_node("orchestrator", orchestrator_node)
        self.graph.add_node("retrieval", retrieval_node)
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
        system_prompt = """You are a knowledge base assistant. Your sole task is to 
        analyze requirements, craft search query if required or simply return 'end' as 
        output if no further research is required."""

        msg_list = state["messages"]

        if state["retrieve_decision"] == True:
            msg_list.append({"search_results": state["retrieval_results"]})

        msg_list.append({"role": "system", "content": system_prompt})

        chat_completion = self.llm_client.chat.completions.create(
            messages= msg_list
            model="llama-3.3-70b-versatile"
        )
        print(chat_completion.choices[0].message.content)
        state["retrieval_query"] = chat_completion.choices[0].message.content
        return

    def decision(self, state: kb_agent_state):
        if state["retrieval_query"] == "end":
            state["retrieve_decision"] = False
            return "end"
        state["retrieve_decision"] = True
        return "retrieve"
        
    def retrieval_node(self, state: kb_agent_state):
        retrieval_results = retrieve_documents(state["retrieval_query"]
        return


