import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def list_mcp_tools():
    """Connect to the MCP server and list available tools."""
    # Create server parameters with the correct format
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"]
    )
    
    # Use stdio_client context manager
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            
            # Print the tools
            print("Available MCP Tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
            
            return tools


if __name__ == "__main__":
    asyncio.run(list_mcp_tools())