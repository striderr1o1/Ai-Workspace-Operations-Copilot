import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("finance_mcp")

@mcp.tool()
async def get_invoice():
    return
