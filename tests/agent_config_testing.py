import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from agents.agent_config import get_orchestrator_client, get_kb_agent, get_booking_agent, get_chat_completion_system_prompt, get_chat_completion
from agents.state import graph_state, orchestrator_output
import instructor
from langsmith.wrappers import wrap_openai
from openai import OpenAI
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain.agents import create_agent

def test_get_orchestrator_client():
    os.environ["OPENROUTER_API_KEY"] = "test-key"
    filepath = os.path.join(os.path.dirname(__file__), "../src/agents/agent_config.py")
    with open(filepath, "r") as file:
        filecontents = file.read()

    updated_content = filecontents.replace("https://openrouter.ai/api/vi", "https://fakeurl.ai/api/v1")

    with open(filepath, "w") as file:
        file.write(updated_content)

    client = get_orchestrator_client()
    with open(filepath, "r") as file:
        filecontents = file.read()

    updated_content = filecontents.replace("https://fakeurl.ai/api/v1", "https://openrouter.ai/api/v1")

    with open(filepath, "w") as file:
        file.write(updated_content)

    mock_client = instructor.from_openai(
            wrap_openai(
                    OpenAI(
                        base_url = "https://fakeurl.ai/api/v1",
                        api_key="test-key"
                        )                
                ),
            mode = instructor.Mode.JSON_SCHEMA,
            )

    assert type(client) == type(mock_client)

def test_get_kb_agent():
    fake_llm = GenericFakeChatModel(messages=iter([AIMessage(content="wow")]))
    agent = get_kb_agent(user_id = "userid-1232131231", supabase_client = None, llm = fake_llm)

    mock_agent = create_agent(model=fake_llm, tools=[])

    assert type(agent) == type(mock_agent)

def test_get_booking_agent():
    fake_llm = GenericFakeChatModel(messages=iter([AIMessage(content="wow")]))
    agent = get_booking_agent(user_id = "userid-1232131231", supabase_client = None, llm = fake_llm)
    mock_agent = create_agent(model=fake_llm, tools=[])
    assert type(agent) == type(mock_agent)

def test_get_chat_completion_system_prompt():
    available_tools = ["booking_agent", "knowledge_base_agent"]
    prompt = get_chat_completion_system_prompt(available_tools)

    assert isinstance(prompt, str)
    assert "You are an orchestrator agent" in prompt
    assert "booking_agent" in prompt
    assert "knowledge_base_agent" in prompt
    assert "return_to_user" in prompt

def test_get_chat_completion():
    fake_client = instructor.from_openai(OpenAI(base_url="https://mockurl.com", api_key="abcd"), mode = instructor.Mode.JSON_SCHEMA)
    state: graph_state = {
        "messages": [{"role": "user", "content": "hi"}],
        "tool_calls": [],
        "knowledge_base_agent_output": "kb output",
        "booking_agent_output": "booking output",
        "return_to_user_decision": False,
        "response_to_user": "",
        "count": 0,
    }
    model = "fakemodel-GPT-2.0"
    response_model = orchestrator_output
    system_prompt = "wowowow"

    response = get_chat_completion(fake_client, state, model, response_model, system_prompt)

    assert response is not None
    assert response.reasoning is str
    assert response.tool_calls is list
    assert response.return_to_user is bool
    assert response.summary_of_agents_response is str

