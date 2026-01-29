from mcp.server.fastmcp import FastMCP
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import os

mcp = FastMCP(name="Time MCP Server")


@mcp.tool()
def fetch_content(url: str) -> dict:
    """Fetches the content of a given URL and returns it as text along with the title."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else None
        
        # Extract text content
        content = soup.get_text()
        
        return {
            "content": content,
            "title": title
        }
    except Exception as e:
        return {
            "content": f"Error fetching content: {str(e)}",
            "title": None
        }

@mcp.tool()
def write_file(content: str, filename: str = None) -> str:
    """Saves text content to a file in the 'docs' directory and returns the filename."""
    try:
        # If no filename is provided, generate one based on timestamp
        if filename is None:
            filename = f"content_{int(datetime.now().timestamp())}.txt"
        
        # Ensure the filename has an extension (.md or .txt)
        if not (filename.endswith('.md') or filename.endswith('.txt')):
            filename += '.txt'
        
        # Create the docs directory if it doesn't exist
        os.makedirs('docs', exist_ok=True)
        
        # Create the full path
        filepath = os.path.join('docs', filename)
        
        # Write the content to the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename
    except Exception as e:
        return f"Error writing file: {str(e)}"


if __name__ == "__main__":
    mcp.run()
