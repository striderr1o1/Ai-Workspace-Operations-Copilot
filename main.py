from KnowledgeBaseTool.kb_tools import ingest_documents, retrieve_documents
from langchain_groq import ChatGroq
from langchain.agents import create_agent

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2
)

tools = [ingest_documents, retrieve_documents]

agent = create_agent(llm, tools = tools, system_prompt="""You are a knowledge base management agent.
Your job is two things: ingest documents when you receive them using the available ingest_documents tool, and the other task is to
retrieve relevant context using the retrieve_documents tool, and answer based on the retrieved context.""")
docs = ['NexCore_Office_Workspace_Report.pdf']
result = agent.invoke({"messages": [{"role": "user", "content": f"can you tell me about NexCore Technologies? their colour scheme?"}]})
print(result)
messages = result.get('message', [])
for msg in messages:
    # Check for AI messages
    if hasattr(msg, 'type') and msg.type == 'ai':
        print("\n" + "="*50)
        print("AI RESPONSE")
        print("="*50)
        
        # Print reasoning if available
        if hasattr(msg, 'additional_kwargs'):
            reasoning = msg.additional_kwargs.get('reasoning_content', '')
            if reasoning:
                print(f"\n🧠 REASONING:\n{reasoning}")
        
        # Print content
        print(f"\n💬 CONTENT:\n{msg.content}")
        
        # Print tool calls if any
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            print(f"\n🔧 TOOL CALLS: {msg.tool_calls}")