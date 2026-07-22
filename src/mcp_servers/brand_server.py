"""Brand & Content Knowledge Agent — MCP tool server (SKELETON).

Backs the Brand agent. All tools are Pinecone-backed retrieval/ingestion.
Bodies are intentionally unimplemented — this file only defines the tool
surface + signatures so the agents can be wired up first.

Run standalone (stdio) via: python brand_server.py
"""

from fastmcp import FastMCP

mcp = FastMCP("BrandKnowledge")


@mcp.tool
def get_all_namespaces() -> list[str]:
    """List the available Pinecone knowledge-base namespaces."""
    # TODO: delegate to KnowledgeBaseTool.kb_tools.get_all_namespaces
    raise NotImplementedError


@mcp.tool
def retrieve_documents(query: str, namespace: str, top_k: int = 5) -> list[dict]:
    """Semantic search over a brand/persona/campaign namespace."""
    # TODO: delegate to KnowledgeBaseTool.retrieval
    raise NotImplementedError


@mcp.tool
def ingest_document(file_path: str, namespace: str) -> dict:
    """Chunk + embed + upsert a document into a namespace."""
    # TODO: delegate to KnowledgeBaseTool.ingestion
    raise NotImplementedError


if __name__ == "__main__":
    mcp.run()
