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

result = agent.invoke({"messages": [{"role": "user", "content": "Can you fetch some data related to Ai?"}]})
print(result)