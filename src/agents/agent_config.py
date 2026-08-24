from langchain_groq import ChatGroq
from langchain.agents import create_agent
from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents
from services.booking_tools import fetch_room_data, insert_room_data
from openai import OpenAI
import os
import instructor
from langsmith.wrappers import wrap_openai
from dotenv import load_dotenv
load_dotenv()



def get_orchestrator_client():
    client = instructor.from_openai(
         wrap_openai(OpenAI(
         base_url="https://openrouter.ai/api/v1",
         api_key=os.environ.get("OPENROUTER_API_KEY"),
         )),
         mode=instructor.Mode.JSON_SCHEMA,
        )
    return client

llm = ChatGroq(
        model = "openai/gpt-oss-20b",
        temperature=0,
        )

def get_kb_agent_system_prompt():
    prompt = """You are a knowledge base agent.
                You answer questions by retrieving relevant documents with the retrieve_documents tool.
                You have no other tools, so you cannot ingest, list, or modify documents — only retrieve them.
                Always call retrieve_documents with a single, focused query string before answering;
                do not answer from memory or guess at content you have not retrieved.
                Base your answer only on what the retrieved documents actually say. If the documents
                don't contain the answer, say so plainly instead of making something up.
                """
    return prompt

def get_booking_agent_system_prompt():
    prompt = """You are a booking agent.
                You manage room/slot reservations for the current user's business using two tools:
                - fetch_room_data: fetches all slots/rooms belonging to the current business, including
                  their time_start, time_end, and occupier_email.
                - insert_room_data: creates a new reservation with a pending status and emails the
                  occupier a confirmation link. It requires time_start and time_end as ISO 8601
                  datetime strings (e.g. '2026-07-31T09:00:00+00:00') and occupier_email.
                You cannot update or delete existing reservations — those tools are not available to you.
                Before inserting a reservation, fetch the current room data if you need to check for
                conflicts. Never invent time_start, time_end, or occupier_email values — ask for
                whatever is missing instead of guessing.
                """
    return prompt

def get_kb_agent(user_id: str, supabase_client, llm: ChatGroq = llm):
    agent = create_agent(
            model=llm,
            tools = [retrieve_documents],
            system_prompt = get_kb_agent_system_prompt(),
            )
    return agent.with_config({"configurable": {"user_id": user_id, "supabase_client": supabase_client}})

def get_booking_agent(user_id: str, supabase_client, llm: ChatGroq = llm):
    agent = create_agent(
            model = llm,
            tools = [fetch_room_data, insert_room_data],
            system_prompt = get_booking_agent_system_prompt(),
            )
    return agent.with_config({"configurable": {"user_id": user_id, "supabase_client": supabase_client}})

def get_chat_completion_system_prompt(available_tools):
    prompt = f"""You are an orchestrator agent.
                You have access to the following agents:
                {available_tools}
                ...
                You will call agents based on user requirement and deliver the answer. Dont call them if not required, and answer yourself then.
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
                    "return_to_user": true/false,
                    "summary_of_agents_response": ""
                }}, you must also include the json curly braces
                
                you will also be provided the responses of sub agents... if the agents have given there results, you will decide to return to the user using the "return_to_user" by setting it to true
                
                - for rooms and reservations related queries, use the booking_agent
                - for retrieval or general knowledge, use the knowledge_base_agent
                - do not pass more than one argument in one tool, for example {{"tool": "booking_agent", "argument": ['pass query in this argument as a single string, dont pass more than one string/query, in essence, this list must contain only one element]
                - you can communicate with the agent through the argument inside of tool in the tool_calls, for example:

                user asks: Fetch me room 1 data...
                your response: 
                {{'reasoning': 'The user wants to fetch room data, which can be done using the booking agent. I will call the booking_agent tool to retrieve the room information.', 'tool_calls': [{{'tool': 'booking_agent', 'argument': ['fetch room data relating to room 1]}}], 'return_to_user': False}}

                - once the called agents have presented with their responses, return the summary using the "summary_of_agents_response". 

                """
    return prompt

def get_chat_completion(llm_client, state, model, response_model, system_prompt):
    response = llm_client.chat.completions.create(
               model=model,
               messages=[{"role": "system", "content": system_prompt}] + state["messages"] + [{"role": "assistant", "content": f"""Agent outputs —
                        knowledge_base_agent: {state['knowledge_base_agent_output']}, booking_agent: {state['booking_agent_output']}"""}],
               response_model=response_model,
               # JSON_SCHEMA mode sends a strict response_format; require_parameters
               # makes OpenRouter route only to providers that actually honour it,
               # instead of falling back to one that returns unconstrained content.
               extra_body={"provider": {"require_parameters": True}},
               )
#    print(response)
    return response
