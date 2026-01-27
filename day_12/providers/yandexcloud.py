import json
from typing import Optional, List, Dict, Any
import aiohttp
import os
import time
import sys
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from .base import Provider
from .completion_response import CompletionsResponse


class YandexCloudProvider(Provider):
    """YandexCloud API provider"""
    
    def __init__(self):
        super().__init__("YandexCloud")
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.folder_id = os.getenv("YANDEXCLOUD_FOLDER_ID", "")
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float, model: str, tools: Optional[List[Dict[str, Any]]] = None) -> Optional[CompletionsResponse]:
        """Call YandexCloud API using REST"""
        if not model:
            model = os.getenv("YANDEXCLOUD_MODEL", "yandexgpt-lite/latest")
        api_key = os.getenv("YANDEXCLOUD_API_KEY", "")
         
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        yandex_messages = []
        for msg in messages:
            yandex_messages.append({"role": msg["role"], "text": msg["content"]})
        
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{model}",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": "1000"
            },
            "messages": yandex_messages
        }
        
        # Add tools to payload if provided
        if tools:
            # Convert tools from MCP format to YandexCloud format
            yandex_tools = []
            for tool in tools:
                yandex_tool = {
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                yandex_tools.append(yandex_tool)
            payload["tools"] = yandex_tools

        print(f"REQUEST: {json.dumps(payload)}")

        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    
                    print(f"RESULT: {json.dumps(result)}")

                    # Check if the response contains tool calls
                    alternative = result["result"]["alternatives"][0]
                    message = alternative["message"]
                    usage = result["result"].get("usage", {})
                    
                    # If this is a tool call, we need to handle it
                    if "toolCallList" in message:
                        # Extract tool calls
                        tool_calls = message["toolCallList"]["toolCalls"]
                        
                        # Call the actual MCP tools
                        tool_results = []
                        for tool_call in tool_calls:
                            function_call = tool_call["functionCall"]
                            tool_name = function_call["name"]
                            arguments = function_call["arguments"]
                            
                            # Call the MCP tool
                            tool_result = await self._call_mcp_tool(tool_name, arguments)
                            tool_results.append({
                                "functionResult": {
                                    "name": tool_name,
                                    "content": tool_result
                                }
                            })
                        
                        # Make another API call with tool results
                        final_response = await self._call_with_tool_results(yandex_messages, tool_results, temperature, model)
                        return final_response
                    else:
                        # Regular text response
                        text = message["text"]
                        return CompletionsResponse(
                            text=text,
                            prompt_tokens=usage.get("inputTextTokens"),
                            completion_tokens=usage.get("completionTokens"),
                            total_tokens=usage.get("totalTokens"),
                            latency=latency
                        )
        except Exception as e:
            print(f"Error calling YandexCloud API: {e}")
            return None
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool and return the result as a string."""
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["mcp_server.py"]
            )
            
            # Use stdio_client context manager
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    
                    # Call the tool
                    result = await session.call_tool(tool_name, arguments)
                    
                    # Extract the result text
                    if result.content:
                        return result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                    else:
                        return "No result"
        except Exception as e:
            print(f"Error calling MCP tool {tool_name}: {e}")
            return f"Error calling tool: {str(e)}"
    
    async def _call_with_tool_results(self, messages: List[Dict[str, Any]], tool_results: List[Dict[str, Any]], temperature: float, model: str) -> Optional[CompletionsResponse]:
        """Make another API call with tool results."""
        api_key = os.getenv("YANDEXCLOUD_API_KEY", "")
         
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Prepare messages with tool results
        yandex_messages = []
        for msg in messages:
            yandex_messages.append({"role": msg["role"], "text": msg["text"] if "text" in msg else msg["content"]})
        
        # Add tool results
        yandex_messages.append({
            "role": "user",
            "toolResultList": {
                "toolResults": tool_results
            }
        })
        
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{model}",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": "1000"
            },
            "messages": yandex_messages
        }
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    
                    print(f"RESULT with tool results: {json.dumps(result)}")
                    
                    # Extract the final response
                    alternative = result["result"]["alternatives"][0]
                    message = alternative["message"]
                    usage = result["result"].get("usage", {})
                    
                    # Return the final text response
                    text = message["text"]
                    return CompletionsResponse(
                        text=text,
                        prompt_tokens=usage.get("inputTextTokens"),
                        completion_tokens=usage.get("completionTokens"),
                        total_tokens=usage.get("totalTokens"),
                        latency=latency
                    )
        except Exception as e:
            print(f"Error calling YandexCloud API with tool results: {e}")
            return None
    
    async def tokenize(self, text: str, model: str) -> Optional[int]:
        """Get token count for the given text using YandexCloud API"""
        # YandexCloud doesn't have a direct tokenize endpoint
        # We'll use the completion endpoint with maxTokens=1 to get token count
        if not model:
            model = os.getenv("YANDEXCLOUD_MODEL", "yandexgpt-lite/latest")
        api_key = os.getenv("YANDEXCLOUD_API_KEY", "")
         
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0,
                "maxTokens": "1"  # We only need to count tokens, not generate text
            },
            "messages": [{"role": "user", "text": text}]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            print(f"Error getting token count from YandexCloud API: {e}")
            return None