import json
from typing import Optional, List, Dict, Any
import aiohttp
import os
import time
import sys
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from util.log_curl import log_curl_request
from .base import Provider
from .completion_response import CompletionsResponse


class YandexCloudProvider(Provider):
    """YandexCloud API provider"""

    def __init__(self):
        super().__init__("YandexCloud")
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.folder_id = os.getenv("YANDEXCLOUD_FOLDER_ID", "")

    def _get_headers(self) -> Dict[str, str]:
        api_key = os.getenv("YANDEXCLOUD_API_KEY", "")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def _convert_messages(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result = []
        for msg in messages:
            text = msg.get("content") or msg.get("text", "")
            result.append({"role": msg["role"], "text": text})
        return result

    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        temperature: float,
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        yandex_messages = self._convert_messages(messages)

        if tool_results:
            yandex_messages.append(
                {"role": "user", "toolResultList": {"toolResults": tool_results}}
            )

        payload = {
            "modelUri": f"gpt://{self.folder_id}/{model}",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": "1000",
            },
            "messages": yandex_messages,
        }

        # print(f"PAYLOAD: {payload}")

        if tools:
            yandex_tools = []
            for tool in tools:
                func = tool.get("function", {})
                yandex_tools.append(
                    {
                        "function": {
                            "name": func.get("name", ""),
                            "description": func.get("description", ""),
                            "parameters": func.get("parameters", {}),
                        }
                    }
                )
            payload["tools"] = yandex_tools

        return payload

    def _extract_response(
        self, result: Dict[str, Any], latency: float
    ) -> CompletionsResponse:
        api_result = result.get("result", result)
        inner_result = api_result.get("result", api_result)
        alternatives = inner_result.get("alternatives", inner_result.get("choices", []))

        if not alternatives:
            print("-" * 50)
            print(json.dumps(result))
            print("-" * 50)
            raise ValueError("No alternatives or choices in response")

        alternative = alternatives[0]
        message = alternative.get("message", alternative)
        usage = api_result.get("usage", {})

        return CompletionsResponse(
            text=message["text"],
            prompt_tokens=usage.get("inputTextTokens"),
            completion_tokens=usage.get("completionTokens"),
            total_tokens=usage.get("totalTokens"),
            latency=latency,
        )

    async def _execute_request(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request and return raw result for further processing."""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                # tc = aiohttp.TraceConfig()
                # log_curl_request(session, tc)
                # session._trace_configs.append(tc)

                async with session.post(
                    self.url, headers=headers, json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    return {"result": result, "latency": latency}
        except Exception as e:
            print(f"Error calling YandexCloud API: {e}")
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
        inner_result = api_result.get("result", api_result)
        alternatives = inner_result.get("alternatives", inner_result.get("choices", []))

        if not alternatives:
            print("-" * 50)
            print(json.dumps(result))
            print("-" * 50)
            raise ValueError("No alternatives or choices in response")

        alternative = alternatives[0]
        message = alternative.get("message", alternative)
        latency = result.get("latency", 0)

        if "toolCallList" not in message:
            return self._extract_response(api_result, latency)

        tool_calls = message["toolCallList"]["toolCalls"]
        yandex_messages = self._convert_messages(messages)
        current_tool_results = []

        for tool_call in tool_calls:
            function_call = tool_call["functionCall"]
            tool_name = function_call["name"]
            arguments = function_call["arguments"]
            tool_result = await self._call_mcp_tool(tool_name, arguments)
            current_tool_results.append(
                {
                    "functionResult": {
                        "name": tool_name,
                        "content": tool_result,
                    }
                }
            )

        all_tool_results = (tool_results or []) + current_tool_results

        headers = self._get_headers()
        payload = self._build_payload(
            yandex_messages, temperature, model, tool_results=all_tool_results
        )
        follow_up = await self._execute_request(payload, headers)

        if follow_up:
            return await self._handle_tool_calls(
                yandex_messages, follow_up, temperature, model, all_tool_results
            )

        return None

    async def completions(
        self,
        messages: List[Dict[str, Any]],
        temperature: float,
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[CompletionsResponse]:
        """Call YandexCloud API using REST"""
        if not model:
            model = os.getenv("YANDEXCLOUD_MODEL", "yandexgpt/latest")

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
        print(f"CALL_TOOL: {tool_name}, {arguments}")
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=sys.executable, args=["mcp_server.py"]
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
