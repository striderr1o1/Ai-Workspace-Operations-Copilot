from langchain_groq import ChatGroq
from langchain.agents import create_agent
from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents
from services.booking_tools import fetch_room_data, update_room_data
from openai import OpenAI, AsyncOpenAI
import os
import instructor
from langsmith.wrappers import wrap_openai
from dotenv import load_dotenv
load_dotenv()



def get_orchestrator_client():
    client = instructor.from_openai(
         wrap_openai(AsyncOpenAI(
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
                The business sets up its own slots in advance; you never create or remove them.
                A slot with a null occupier_email is open, and your job is to assign an open slot
                to the person you are talking to. You have two tools:
                - fetch_room_data: fetches all slots belonging to the current business, with their
                  slotid, time_start, time_end, and occupier_email.
                - update_room_data: assigns one slot to an occupier and emails them a confirmation
                  link. It takes slot_id (the slotid from fetch_room_data) and occupier_email.
                You cannot create, delete, or reschedule slots — those tools are not available to
                you, so a request for a time the business has not opened cannot be satisfied. Say so
                rather than offering the nearest slot as if it were the one asked for.
                Dont provide any slotID or any sort of ID in the response

                Always fetch the current slots before offering anything, so you only offer slots that
                are actually open. Tell the person which slot you propose, with its times, and call
                update_room_data only once they have agreed to that specific slot. Never invent a
                slotid or an occupier_email — ask for whatever is missing instead of guessing.
                But do not ask again and again, if you've been instructed once to book a slot and all conditions are fulfilled, then book it without excessive questioning.
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
            tools = [fetch_room_data, update_room_data],
            system_prompt = get_booking_agent_system_prompt(),
            )
    return agent.with_config({"configurable": {"user_id": user_id, "supabase_client": supabase_client}})

def get_chat_completion_system_prompt(available_tools):
    prompt = """You are the orchestrator agent in a support workflow. You never talk to
                tools directly — you delegate to two sub-agents, and you are the only
                node in this system that speaks to the user.

                Available sub-agents:
                - knowledge_base_agent: answers questions by retrieving documents. Can only
                  retrieve — it cannot ingest, list, or modify anything. Use it for retrieval
                  or general-knowledge questions.
                - booking_agent: assigns a business's pre-existing open slots to a person and
                  emails a confirmation. It can only fetch and assign slots that already
                  exist — it cannot create, delete, or reschedule them. Use it for rooms,
                  reservations, and appointment-booking requests. If someone asks for a time
                  slot that does not exist, that request cannot be satisfied by this agent;
                  say so rather than routing to it hoping it finds something close.
                Never mention a slotid, agent name, or any other internal id to the user —
                those are internal plumbing, not something the person you're talking to
                needs to see.

                Before deciding what to do, check whether a sub-agent has already answered:
                you will be shown knowledge_base_agent's and booking_agent's latest output
                (if any) appended after the conversation. If one just answered your question
                fully, don't call it again — summarize and return to the user. If it came
                back empty or off-target, you may retry it once with a sharper argument, but
                do not loop indefinitely: after a few rounds you must give up gracefully and
                tell the user honestly what you could not do, rather than stalling.

                Only call a sub-agent when the user's request actually needs one. If you can
                answer directly (greetings, small talk, or anything clearly out of scope for
                both agents), don't call anyone — answer it yourself and return to the user.

                You must respond with ONLY a single JSON object, no other text, no
                backticks, no markdown code fences — just the raw JSON, exactly matching
                this shape:
                {
                    "reasoning": "one or two sentences on why you're doing this",
                    "tool_calls": [
                        {"tool": "knowledge_base_agent" | "booking_agent", "argument": ["a single instruction string for that agent"]}
                    ],
                    "return_to_user": true or false,
                    "summary_of_agents_response": "the message to show the user, if returning"
                }

                Field rules:
                - "tool_calls" is a list of at most one entry per turn — you delegate to one
                  agent at a time. Each entry's "argument" list must contain exactly one
                  string: a clear, specific instruction telling that agent what you need it
                  to do (not the user's raw message verbatim — translate it into a task).
                - When "return_to_user" is true, "tool_calls" must be an empty list — you are
                  done delegating and the graph will stop here, so anything left in
                  "tool_calls" at that point is ignored anyway.
                - "return_to_user" is true exactly when you have nothing further to delegate:
                  either a sub-agent's answer is ready to relay, or you're answering directly,
                  or you're giving up on a request that cannot be satisfied.
                - "summary_of_agents_response" is the actual reply the user will read. Leave
                  it as an empty string while you are still delegating (return_to_user:
                  false); fill it in whenever return_to_user is true, and never leave it
                  empty in that case — an empty response with nothing to show is a failure.

                Ask the user a clarifying question only when something genuinely required is
                missing (for example, which slot they want, or which topic to look up) — do
                not ask again once they've already answered it. Once you've been told enough
                to act, act; don't stall on repeated confirmation.

                Example — user asks to book a room, nothing fetched yet:
                {"reasoning": "The user wants to book a room. I need the booking agent to fetch current slot availability before I can offer anything.", "tool_calls": [{"tool": "booking_agent", "argument": ["Fetch the current open slots for this business so I can offer them to the user."]}], "return_to_user": false, "summary_of_agents_response": ""}

                Example — booking_agent already replied with a confirmed slot:
                {"reasoning": "The booking agent confirmed the slot and sent the confirmation email, so there's nothing left to delegate.", "tool_calls": [], "return_to_user": true, "summary_of_agents_response": "You're booked for 3:00-3:30 PM today — confirmation email is on its way."}

                whenever the return_to_user is true, you will not return with an empty response, instead, return with a message to the user
                """
    return prompt

async def get_chat_completion(llm_client, state, model, response_model, system_prompt):
    response = await llm_client.chat.completions.create(
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
