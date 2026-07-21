from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents, get_all_namespaces
from openai import OpenAI
import os
import instructor
from dotenv import load_dotenv
load_dotenv()



def get_orchestrator_client():
    client = instructor.from_openai(
         OpenAI(
         base_url="https://openrouter.ai/api/v1",
         api_key=os.environ.get("OPENROUTER_API_KEY"),
         ),
         mode=instructor.Mode.JSON,
        )
    return client

llm = ChatGroq(
        model = "openai/gpt-oss-20b",
        temperature=0,
        )


def get_mcp_client():
    """Build the MCP client used to reach the tool servers (e.g. Hubspot MCP)."""
    client = MultiServerMCPClient(
        {
            "hubspot": {
                "url": os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp"),
                "transport": "stdio",
            }
        }
    )
    return client


async def get_mcp_tools():
    """Fetch the tools exposed by the MCP server(s) as LangChain tools."""
    client = get_mcp_client()
    tools = await client.get_tools()
    return tools


def get_kb_agent(tools=None):
    agent = create_agent(
            model=llm,
            tools = [get_all_namespaces, retrieve_documents] + list(tools or []),
            )
    return agent

def get_booking_agent(tools=None):
    agent = create_agent(
            model = llm,
            tools = list(tools or []),
            )
    return agent

def get_finance_agent():
    agent = create_agent(
            model = llm, 
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
                    "return_to_user": true/false,
                    "summary_of_agents_response": ""
                }}, you must also include the json curly braces
                
                you will also be provided the responses of sub agents... if the agents have given there results, you will decide to return to the user using the "return_to_user" by setting it to true
                
                - for rooms and reservations related queries, use the booking_agent
                - for retrieval or general knowledge, use the knowledge_base_agent
                - do not answer on your own without calling sub agents
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
               )

    return response
