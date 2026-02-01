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


class OllamaProvider(Provider):
    """Ollama API provider"""

    def __init__(self):
        super().__init__("Ollama")
        self.url = "http://localhost:11434/v1/chat/completions"

    def _get_headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    def _convert_messages(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result = []
        for msg in messages:
            text = msg.get("content") or msg.get("text", "")
            result.append({"role": msg["role"], "content": text})
        return result

    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        temperature: float,
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        ollama_messages = self._convert_messages(messages)

        if tool_results:
            ollama_messages.append(
                {"role": "user", "content": json.dumps(tool_results)}
            )

        payload = {
            "model": model,
            "messages": ollama_messages,
            "temperature": temperature,
        }

        if tools:
            payload["tools"] = tools

        return payload

    def _extract_response(
        self, result: Dict[str, Any], latency: float
    ) -> CompletionsResponse:
        message = result["choices"][0]["message"]
        text = message.get("content", "")
        usage = result.get("usage", {})

        return CompletionsResponse(
            text=text,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            latency=latency,
        )

    async def _execute_request(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request and return raw result for further processing."""
        start_time = time.time()
        try:
            print(f"PAYLOAD: {json.dumps(payload, indent=2, ensure_ascii=False)[:500]}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url, headers=headers, json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    return {"result": result, "latency": latency}
        except aiohttp.ClientConnectorError:
            print(
                "Error: Could not connect to Ollama. Please ensure Ollama is running on localhost:11434"
            )
            return None
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                print(
                    f"Error: Model not found. Please pull the model first with 'ollama pull <model>'"
                )
            else:
                print(f"Error calling Ollama API: {e}")
            return None
        except Exception as e:
            print(f"Error calling Ollama API: {e}")
            return None

    async def _handle_tool_calls(
        self,
        messages: List[Dict[str, Any]],
        result: Dict[str, Any],
        temperature: float,
        model: str,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[CompletionsResponse]:
        """Handle tool calls in the response, recursively if needed."""
        api_result = result.get("result", result)
        choices = api_result.get("choices", [])

        if not choices:
            print("-" * 50)
            print(json.dumps(result))
            print("-" * 50)
            raise ValueError("No choices in response")

        message = choices[0].get("message", choices[0])
        latency = result.get("latency", 0)

        tool_calls = message.get("tool_calls")

        if not tool_calls:
            return self._extract_response(api_result, latency)

        ollama_messages = self._convert_messages(messages)
        ollama_messages.append(
            {"role": "assistant", "content": message.get("content", "")}
        )

        current_tool_results = []

        for tool_call in tool_calls:
            function_call = tool_call.get("function", {})
            tool_name = function_call.get("name", "")
            arguments = function_call.get("arguments", "")
            tool_result = await self._call_mcp_tool(tool_name, arguments)
            current_tool_results.append(
                {
                    "role": "tool",
                    "content": json.dumps({"name": tool_name, "result": tool_result}),
                }
            )

        all_tool_results = (tool_results or []) + current_tool_results

        headers = self._get_headers()
        payload = self._build_payload(
            ollama_messages, temperature, model, tool_results=all_tool_results
        )
        follow_up = await self._execute_request(payload, headers)

        if follow_up:
            return await self._handle_tool_calls(
                ollama_messages, follow_up, temperature, model, all_tool_results
            )

        return None

    async def completions(
        self,
        messages: List[Dict[str, Any]],
        temperature: float,
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[CompletionsResponse]:
        """Call Ollama API using REST"""
        if not model:
            model = os.getenv("OLLAMA_MODEL", "minimax-m2.1:cloud")

        print(f"MODEL: {model}")

        headers = self._get_headers()
        payload = self._build_payload(messages, temperature, model, tools)

        result = await self._execute_request(payload, headers)
        if result:
            return await self._handle_tool_calls(
                messages, result, temperature, model, None
            )
        return None

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool and return the result as a string."""
        print(f"CALL_TOOL: {tool_name}")
        try:
            server_params = StdioServerParameters(
                command=sys.executable, args=["mcp_server.py"]
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)

                    if result.content:
                        content_item = result.content[0]
                        text_content = getattr(content_item, "text", None)
                        ret = text_content if text_content else str(content_item)
                        print(ret)
                        return ret
                    else:
                        ret = "No result"
                        print(ret)
                        return ret
        except Exception as e:
            print(f"Error calling MCP tool {tool_name}: {e}")
            return f"Error calling tool: {str(e)}"
