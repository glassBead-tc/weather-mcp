from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ultra-minimal-server")

@mcp.tool()
def ping() -> Dict[str, Any]:
    """Simple ping tool that returns a greeting."""
    return {"message": "Hello from ultra-minimal MCP server!", "status": "active"}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")