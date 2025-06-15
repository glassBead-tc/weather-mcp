from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ultra-minimal")

@mcp.tool()
def ping() -> str:
    """Simple ping tool."""
    return "pong"

if __name__ == "__main__":
    mcp.run(transport="shttp")