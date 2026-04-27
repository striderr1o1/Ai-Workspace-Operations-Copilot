from langchain_groq import ChatGroq
from langchain.agents import create_agent
from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents
from services.supabase_client import fetch_room_data, insert_room_data
from openai import OpenAI
import os
import instructor
from dotenv import load_dotenv
load_dotenv()



def get_subagents_client():
    client = instructor.from_openai(
         OpenAI(
         base_url="https://openrouter.ai/api/v1",
         api_key=os.environ.get("OPENROUTER_API_KEY"),
         ),
         mode=instructor.Mode.JSON,
        )
    return client

llm = ChatGroq(
        model = "qwen/qwen3-32b",
        temperature=0,
        )

def get_kb_agent():
    agent = create_agent(
            model=llm,
            tools = [retrieve_documents],
            )
    return agent

def get_booking_agent():
    agent = create_agent(
            model = llm,
            tools = [fetch_room_data, insert_room_data]
            )
    return agent

def get_chat_completion_system_prompt(available_tools):
    prompt = f"""You are an orchestrator agent.
                You have access to the following agents:
                {available_tools}
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
    return prompt

def get_chat_completion(llm_client, state, model, response_model, system_prompt):
    response = llm_client.chat.completions.create(
               model=model,
               messages=[{"role": "system", "content": system_prompt}] + state["messages"] + [{"role": "user", "content": f"""Agent outputs — 
                        knowledge_base_agent: {state['knowledge_base_agent_output']}, booking_agent: {state['booking_agent_output']},
                        finance_agent: {state['finance_agent_output']}"""}],
               response_model=response_model,
               )

    return response
