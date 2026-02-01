#!/usr/bin/env python3
"""
MCP Server for AI-assisted programming utility.
Provides tools for file operations and shell script execution in the 'out' subfolder.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Base directory for file operations (directory containing this script)
BASE_DIR = Path(__file__).parent.resolve()
OUT_DIR = BASE_DIR / "out"
OUT_DIR.mkdir(exist_ok=True)

app = Server("ai-assist-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="write_file",
            description="Write content to a file. Creates the file if it doesn't exist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename (e.g., 'quick_sort.py' or 'subfolder/file.txt')",
                    },
                    "content": {
                        "type": "string",
                        "description": "File content to write",
                    },
                },
                "required": ["filename", "content"],
            },
        ),
        Tool(
            name="execute_shell",
            description="Execute a shell command",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute (e.g., 'ls -la', 'python script.py')",
                    }
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="read_file",
            description="Read content from a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Filename"}
                },
                "required": ["filename"],
            },
        ),
        Tool(
            name="list_files",
            description="List files",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Optional subdirectory path",
                    }
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "write_file":
            filename = arguments.get("filename", "")
            content = arguments.get("content", "")

            # Security: prevent path traversal
            if ".." in filename or filename.startswith("/"):
                return [
                    TextContent(
                        type="text", text=f"Error: Invalid filename '{filename}'"
                    )
                ]

            # Ensure file is within out directory
            out_path = OUT_DIR / filename
            if not out_path.resolve().is_relative_to(OUT_DIR.resolve()):
                return [
                    TextContent(
                        type="text",
                        text=f"Error: File path '{filename}' is outside the allowed directory",
                    )
                ]

            # Create parent directories if needed
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            out_path.write_text(content)

            relative_path = out_path.relative_to(OUT_DIR)
            return [TextContent(type="text", text=f"Done. Saved to ./{relative_path}")]

        elif name == "execute_shell":
            command = arguments.get("command", "")

            # Security: prevent dangerous commands
            dangerous_patterns = ["rm -rf", "rm /", "mkfs", "dd if="]
            for pattern in dangerous_patterns:
                if pattern in command:
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: Dangerous command blocked: {pattern}",
                        )
                    ]

            # Execute command in out directory
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(OUT_DIR),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                output = f"Command: {command}\nExit code: {result.returncode}\n"
                if result.stdout:
                    output += f"Stdout:\n{result.stdout}"
                if result.stderr:
                    output += f"\nStderr:\n{result.stderr}"

                return [TextContent(type="text", text=output)]
            except subprocess.TimeoutExpired:
                return [
                    TextContent(
                        type="text", text="Error: Command timed out after 30 seconds"
                    )
                ]
            except Exception as e:
                return [
                    TextContent(type="text", text=f"Error executing command: {str(e)}")
                ]

        elif name == "read_file":
            filename = arguments.get("filename", "")

            # Security checks
            if ".." in filename or filename.startswith("/"):
                return [
                    TextContent(
                        type="text", text=f"Error: Invalid filename '{filename}'"
                    )
                ]

            out_path = OUT_DIR / filename
            if not out_path.resolve().is_relative_to(OUT_DIR.resolve()):
                return [
                    TextContent(
                        type="text",
                        text=f"Error: File path '{filename}' is outside the allowed directory",
                    )
                ]

            if not out_path.exists():
                return [
                    TextContent(type="text", text=f"Error: File '{filename}' not found")
                ]

            content = out_path.read_text()
            relative_path = out_path.relative_to(OUT_DIR)
            return [
                TextContent(type="text", text=f"File: ./{relative_path}\n\n{content}")
            ]

        elif name == "list_files":
            path = arguments.get("path", "")

            # Security checks
            if ".." in path or path.startswith("/"):
                return [TextContent(type="text", text=f"Error: Invalid path '{path}'")]

            list_path = OUT_DIR / path if path else OUT_DIR
            if not list_path.resolve().is_relative_to(OUT_DIR.resolve()):
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Path '{path}' is outside the allowed directory",
                    )
                ]

            if not list_path.exists():
                return [
                    TextContent(type="text", text=f"Error: Path '{path}' not found")
                ]

            if not list_path.is_dir():
                return [
                    TextContent(type="text", text=f"Error: '{path}' is not a directory")
                ]

            files = []
            for item in sorted(list_path.iterdir()):
                rel_path = item.relative_to(OUT_DIR)
                files.append(f"./{rel_path}")

            return [
                TextContent(
                    type="text",
                    text=f"Files in ./{list_path.relative_to(OUT_DIR)}:\n"
                    + "\n".join(files),
                )
            ]

        else:
            return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server with stdio transport"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
