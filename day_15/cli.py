#!/usr/bin/env python3
"""
Command-line dialog UI for AI-assisted programming.
Connects to AI providers and uses MCP tools for file operations and shell execution.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
# logger = logging.getLogger("ai-assist-cli")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from providers.yandexcloud import YandexCloudProvider
from providers.ollama import OllamaProvider
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

load_dotenv()


class AIAssistCLI:
    def __init__(self, provider_name: str = "yandexcloud"):
        self.provider_name = provider_name
        self.session: Optional[ClientSession] = None
        self.server_process = None

        self.mcp_tools = [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file. Creates the file and any missing parent directories if they don't exist. Examples: 'quick_sort.py', 'utils/helper.py', 'api/server/main.py'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Filename - can include subdirectories like 'subdir/nested/file.py'",
                            },
                            "content": {
                                "type": "string",
                                "description": "File content to write",
                            },
                        },
                        "required": ["filename", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_shell",
                    "description": "Execute a shell command. Use for testing, running scripts, listing files, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute",
                            }
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read content from a file. Supports files in subdirectories.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Filename - can include subdirectories like 'utils/helper.py'",
                            }
                        },
                        "required": ["filename"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List files. Optionally list files in a specific subdirectory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Optional subdirectory path (e.g., 'utils' or 'api/server')",
                            }
                        },
                    },
                },
            },
        ]

    async def start_mcp_server(self):
        """Start the MCP server as a subprocess"""
        script_dir = Path(__file__).parent

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(script_dir / "mcp_server.py")],
            cwd=str(script_dir),
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                self.session = session
                await session.initialize()
                print("MCP Server connected. Ready to assist!", file=sys.stderr)
                await self.chat_loop()

    async def chat_loop(self):
        """Main chat loop"""
        messages = [
            {
                "role": "system",
                "content": """You are an AI programming assistant. You help users write code and execute shell commands using the provided MCP tools.

When users ask you to create files or run commands:
1. Always use the write_file tool to create files
2. Use execute_shell to run commands when needed (testing, listing files, etc.)
3. Report success with the exact format: "Done. Saved to ./filename" for each file created
4. You can make multiple tool calls in sequence or parallel

For file operations:
- Always use relative paths (e.g., 'main.py', 'utils/helper.py')
- Create complete, working code
- Include necessary imports and dependencies

For shell operations:
- Use 'ls -la' to list files
- Use appropriate commands to test or run code
- Keep commands simple and focused""",
            }
        ]

        print("\n=== AI Programming Assistant ===")
        print("Type your request (or 'quit' to exit):")
        print("Examples:")
        print("  'Make a quick sort in python and run it'")
        print("  'Create simple server with Python and FastAPI, also create Dockerfile and docker-compose.yml. Run it in Docker.'")
        print("  'List files'")
        print("================================\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            # Add user message to history
            messages.append({"role": "user", "content": user_input})

            try:
                provider = self._create_provider()
                model = self._get_model_for_provider(self.provider_name)

                # logger.info(f"[MODEL INPUT] model={model}, messages_count={len(messages)}")
                # logger.info(f"[MODEL INPUT] last_user_message: {messages[-1]['content'][:200] if messages[-1].get('content') else 'N/A'}...")

                response = await provider.completions(
                    messages=messages,
                    temperature=0.1,
                    model=model,
                    tools=self.mcp_tools,
                )

                # logger.info(f"[MODEL OUTPUT] response received")

                if response:
                    if hasattr(response, "choices") and response.choices:
                        assistant_message = response.choices[0].message
                        tool_calls_attr = getattr(assistant_message, "tool_calls", None)
                        if tool_calls_attr and isinstance(tool_calls_attr, list):
                            # logger.info(f"[MODEL OUTPUT] tool_calls count: {len(tool_calls_attr)}")
                            await self.handle_tool_calls(tool_calls_attr, messages)
                        else:
                            content = getattr(assistant_message, "content", None)
                            if content is None and isinstance(assistant_message, dict):
                                content = assistant_message.get("content", "")
                            if not content:
                                content = str(assistant_message)
                            if content:
                                # logger.info(f"[MODEL OUTPUT] text response: {content[:200]}...")
                                print(f"\nAssistant: {content}\n")
                                messages.append(
                                    {"role": "assistant", "content": content}
                                )
                    elif hasattr(response, "text"):
                        text = response.text
                        if hasattr(response, "tool_calls") and response.tool_calls:
                            # logger.info(f"[MODEL OUTPUT] tool_calls count: {len(response.tool_calls)}")
                            await self.handle_tool_calls(response.tool_calls, messages)
                        elif text:
                            # logger.info(f"[MODEL OUTPUT] text response: {text[:200]}...")
                            print(f"\nAssistant: {text}\n")
                            messages.append({"role": "assistant", "content": text})

            except Exception as e:
                print(f"\nError: {e}\n")

    async def handle_tool_calls(
        self, tool_calls: List[Any], messages: List[Dict[str, Any]]
    ):
        """Handle MCP tool calls from the AI"""
        tool_results = []

        for tool_call in tool_calls:
            # Handle both dict and object formats
            if isinstance(tool_call, dict):
                tool_name = tool_call.get("function", {}).get("name", "")
                arguments_str = tool_call.get("function", {}).get("arguments", "{}")
            else:
                func_obj = getattr(tool_call, "function", None)
                if func_obj is None:
                    tool_name = ""
                    arguments_str = "{}"
                elif isinstance(func_obj, dict):
                    tool_name = func_obj.get("name", "")
                    arguments_str = func_obj.get("arguments", "{}")
                else:
                    tool_name = getattr(func_obj, "name", "")
                    arguments_str = getattr(func_obj, "arguments", "{}")

            try:
                arguments = (
                    json.loads(arguments_str)
                    if isinstance(arguments_str, str)
                    else arguments_str
                )
            except json.JSONDecodeError:
                arguments = {}

            print(f"\n[Tool Call: {tool_name}]", file=sys.stderr)
            # logger.info(f"[TOOL CALL] name={tool_name}, arguments={json.dumps(arguments, indent=2)}")

            try:
                if self.session:
                    result = await self.session.call_tool(tool_name, arguments)
                    if result.content:
                        first_content = result.content[0]
                        if isinstance(first_content, dict):
                            tool_output = first_content.get("text", "")
                        else:
                            tool_output = getattr(first_content, "text", "")
                    else:
                        tool_output = ""

                    # logger.info(f"[TOOL RESULT] name={tool_name}, output={tool_output[:200]}..." if len(tool_output) > 200 else f"[TOOL RESULT] name={tool_name}, output={tool_output}")
                    print(f"[Result] {tool_output}", file=sys.stderr)

                    tool_results.append(
                        {
                            "role": "tool",
                            "content": tool_output,
                            "tool_call_id": tool_call.get("id", "")
                            if isinstance(tool_call, dict)
                            else (
                                getattr(tool_call, "id", "")
                                if hasattr(tool_call, "id")
                                else ""
                            ),
                            "name": tool_name,
                        }
                    )

            except Exception as e:
                print(f"\n[Tool Error] {e}\n", file=sys.stderr)
                tool_results.append(
                    {
                        "role": "tool",
                        "content": f"Error: {str(e)}",
                        "tool_call_id": tool_call.get("id", "")
                        if isinstance(tool_call, dict)
                        else (
                            getattr(tool_call, "id", "")
                            if hasattr(tool_call, "id")
                            else ""
                        ),
                        "name": tool_name,
                    }
                )

        if tool_results:
            messages.extend(tool_results)

            provider = self._create_provider()
            model = self._get_model_for_provider(self.provider_name)

            # logger.info(f"[MODEL INPUT (TOOL FOLLOW-UP)] model={model}, messages_count={len(messages)}")

            response = await provider.completions(
                messages=messages, temperature=0.7, model=model, tools=self.mcp_tools
            )

            # logger.info(f"[MODEL OUTPUT (TOOL FOLLOW-UP)] response received")

            if response:
                if hasattr(response, "choices") and response.choices:
                    assistant_message = response.choices[0].message
                    content = ""
                    if hasattr(assistant_message, "content"):
                        content = getattr(assistant_message, "content", "") or ""
                    elif isinstance(assistant_message, dict):
                        content = assistant_message.get("content", "") or ""

                    if content:
                        # logger.info(f"[MODEL OUTPUT (TOOL FOLLOW-UP)] text response: {content[:200]}...")
                        print(f"\nAssistant: {content}\n")
                        messages.append({"role": "assistant", "content": content})

                    tool_calls_attr = None
                    tool_calls_attr = (
                        getattr(assistant_message, "tool_calls", None)
                        if hasattr(assistant_message, "tool_calls")
                        else None
                    )
                    if tool_calls_attr is None and isinstance(assistant_message, dict):
                        tool_calls_attr = assistant_message.get("tool_calls")

                    if tool_calls_attr:
                        # logger.info(f"[MODEL OUTPUT (TOOL FOLLOW-UP)] nested tool_calls count: {len(tool_calls_attr)}")
                        await self.handle_tool_calls(tool_calls_attr, messages)
                elif hasattr(response, "text"):
                    text = response.text
                    if hasattr(response, "tool_calls") and response.tool_calls:
                        # logger.info(f"[MODEL OUTPUT (TOOL FOLLOW-UP)] tool_calls count: {len(response.tool_calls)}")
                        await self.handle_tool_calls(response.tool_calls, messages)
                    elif text:
                        # logger.info(f"[MODEL OUTPUT (TOOL FOLLOW-UP)] text response: {text[:200]}...")
                        print(f"\nAssistant: {text}\n")
                        messages.append({"role": "assistant", "content": text})

    def _create_provider(self):
        """Create the specified AI provider"""
        providers = {
            "yandexcloud": YandexCloudProvider(),
            "ollama": OllamaProvider(),
        }
        return providers.get(self.provider_name, providers["yandexcloud"])

    def _get_model_for_provider(self, provider_name: str) -> str:
        """Get the model name for the specified provider"""
        models = {
            "yandexcloud": os.getenv("YANDEXCLOUD_MODEL", "aliceai-llm/latest"),
            "ollama": os.getenv("OLLAMA_MODEL", "glm-4.7-flash:latest"),
        }
        return models.get(provider_name, models["yandexcloud"])


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Programming Assistant CLI")
    parser.add_argument(
        "--provider",
        "-p",
        default="yandexcloud",
        choices=["yandexcloud", "ollama"],
        help="AI provider to use (default: yandexcloud)",
    )

    args = parser.parse_args()

    cli = AIAssistCLI(provider_name=args.provider)
    await cli.start_mcp_server()


if __name__ == "__main__":
    asyncio.run(main())
