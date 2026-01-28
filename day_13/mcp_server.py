from mcp.server.fastmcp import FastMCP
from datetime import datetime, timezone

mcp = FastMCP(name="Time MCP Server")


@mcp.tool()
def get_current_time() -> str:
    """Returns the current time in ISO 8601 UTC format."""
    return datetime.now(timezone.utc).isoformat()


@mcp.tool()
def reverse_string(input_string: str) -> str:
    """Reverses any input string and returns it."""
    return f"__{input_string[::-1]}__" 


if __name__ == "__main__":
    mcp.run()
