import os
import asyncio
import chainlit as cl
from chainlit.input_widget import TextInput, Select
from providers.yandexcloud import YandexCloudProvider
from dotenv import load_dotenv
import subprocess
import sys
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# Load environment variables
load_dotenv()

# Initialize the YandexCloud provider
provider = YandexCloudProvider()

# MCP Server management
mcp_session = None
mcp_stdio_transport = None
mcp_stdio_context = None
mcp_server_params = None
mcp_session_context = None

async def start_mcp_server():
    """Start the MCP server and create a session"""
    global mcp_session, mcp_stdio_transport, mcp_stdio_context, mcp_server_params, mcp_session_context
    
    print("Starting MCP server...")
    mcp_server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"]
    )
    
    try:
        # Use stdio_client context manager similar to mcp_client.py
        mcp_stdio_context = stdio_client(mcp_server_params)
        print("MCP stdio context created")
        
        # Enter the stdio context
        stdio_transport = await mcp_stdio_context.__aenter__()
        print("MCP stdio transport entered")
        stdio_read, stdio_write = stdio_transport
        
        mcp_stdio_transport = stdio_transport
        mcp_session = ClientSession(stdio_read, stdio_write)
        print("MCP session created, initializing...")
        
        # Enter the session context
        mcp_session_context = await mcp_session.__aenter__()
        print("MCP session context entered")
        
        # Initialize the session with timeout
        import asyncio
        try:
            await asyncio.wait_for(mcp_session.initialize(), timeout=30.0)
            print("MCP session initialized successfully")
            return mcp_session
        except asyncio.TimeoutError:
            print("MCP session initialization timed out")
            await stop_mcp_server()
            return None
    except Exception as e:
        print(f"MCP server start failed: {e}")
        await stop_mcp_server()
        return None

async def stop_mcp_server():
    """Stop the MCP server and close the session"""
    global mcp_session, mcp_stdio_transport, mcp_stdio_context, mcp_session_context
    
    # First close the session context if it exists
    if mcp_session_context:
        try:
            await mcp_session_context.__aexit__(None, None, None)
        except Exception as e:
            print(f"Error closing session context: {e}")
        finally:
            mcp_session_context = None
    
    # Then close the transport streams
    if mcp_stdio_transport:
        try:
            mcp_stdio_transport[0].close()
            mcp_stdio_transport[1].close()
        except Exception as e:
            print(f"Error closing transport streams: {e}")
        finally:
            mcp_stdio_transport = None
    
    # Finally close the async context (this properly closes the async generator)
    if mcp_stdio_context:
        try:
            await mcp_stdio_context.__aexit__(None, None, None)
        except Exception as e:
            print(f"Error closing stdio context: {e}")
        finally:
            mcp_stdio_context = None
    
    mcp_session = None
    mcp_stdio_transport = None
    mcp_stdio_context = None
    mcp_session_context = None
    mcp_server_params = None

async def get_mcp_tools():
    """Get available tools from MCP server"""
    global mcp_session
    if mcp_session:
        try:
            tools = await mcp_session.list_tools()
            return tools
        except Exception as e:
            print(f"Error getting MCP tools: {e}")
            return []
    return []

async def call_mcp_tool(tool_name: str, arguments: dict = None):
    """Call an MCP tool"""
    global mcp_session
    if mcp_session:
        try:
            result = await mcp_session.call_tool(tool_name, arguments or {})
            return result
        except Exception as e:
            print(f"Error calling MCP tool {tool_name}: {e}")
            return None
    return None


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    print("Chat start called")
    # Start MCP server
    try:
        mcp_started = await start_mcp_server()
        if mcp_started:
            print("MCP Server started successfully")
            await cl.Message(content="🟢 MCP сервер запущен").send()
        else:
            print("MCP Server failed to start")
            await cl.Message(content="⚠️ MCP сервер не запущен").send()
    except Exception as e:
        print(f"MCP Server Error: {e}")
        import traceback
        traceback.print_exc()
        await cl.Message(content=f"⚠️ MCP сервер не запущен: {str(e)}").send()
    
    # Set initial settings
    await cl.ChatSettings(
        [
            TextInput(
                id="temperature",
                label="Температура",
                initial="0.7",
                description="Контролирует случайность ответов (0.0-1.0)",
            ),
            Select(
                id="model",
                label="Модель",
                values=["yandexgpt-lite/latest", "yandexgpt/latest"],
                initial="yandexgpt-lite/latest",
            ),
        ]
    ).send()

    # Send welcome message
    await cl.Message(
        content="👋 Привет! Я готов к общению. Чем могу помочь?"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages"""
    user_content = message.content

    # Create a placeholder for the AI response
    response_placeholder = cl.Message(content="")
    await response_placeholder.send()

    # Get settings from environment or use defaults
    temperature = float(os.getenv("YANDEXCLOUD_TEMPERATURE", "0.7"))
    model = os.getenv("YANDEXCLOUD_MODEL", "yandexgpt-lite/latest")

    # Show typing indicator
    await response_placeholder.stream_token("🤔 Думаю...")

    # Get MCP tools and format them for the system prompt
    mcp_tools = await get_mcp_tools()
    tools_description = ""
    if mcp_tools and mcp_tools.tools:
        tools_description = "\n\nДоступные инструменты MCP:\n"
        for tool in mcp_tools.tools:
            tools_description += f"- {tool.name}: {tool.description}\n"

    # Enhanced system prompt with MCP tools
    system_prompt = "Ты полезный ассистент." + tools_description
    if mcp_tools and mcp_tools.tools:
        system_prompt += "\n\nЕсли пользователь спрашивает время, используй инструмент get_current_time."

    # Simple conversation history with system prompt
    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    # Check if user wants to use MCP tool
    should_use_mcp = False
    mcp_result = None
    if mcp_session and mcp_tools and mcp_tools.tools:
        tool_names = [t.name for t in mcp_tools.tools]
        if "get_current_time" in tool_names and ("время" in user_content.lower() or "time" in user_content.lower()):
            should_use_mcp = True
            mcp_result = await call_mcp_tool("get_current_time")
            if mcp_result and mcp_result.content:
                mcp_result_text = mcp_result.content[0].text if hasattr(mcp_result.content[0], 'text') else str(mcp_result.content[0])
                user_content_with_mcp = f"{user_content}\n\nТекущее время: {mcp_result_text}"
                history[-1] = {"role": "user", "content": user_content_with_mcp}
        elif "reverse_string" in tool_names and ("переверни" in user_content.lower() or "reverse" in user_content.lower()):
            should_use_mcp = True
            # Extract string to reverse from user content
            string_to_reverse = user_content
            if ":" in user_content:
                string_to_reverse = user_content.split(":", 1)[1].strip()
            mcp_result = await call_mcp_tool("reverse_string", {"input_string": string_to_reverse})
            if mcp_result and mcp_result.content:
                mcp_result_text = mcp_result.content[0].text if hasattr(mcp_result.content[0], 'text') else str(mcp_result.content[0])
                user_content_with_mcp = f"{user_content}\n\nПеревернутая строка: {mcp_result_text}"
                history[-1] = {"role": "user", "content": user_content_with_mcp}

    # Call the YandexCloud API
    api_key = os.getenv("YANDEXCLOUD_API_KEY", "")
    folder_id = os.getenv("YANDEXCLOUD_FOLDER_ID", "")
    
    if not api_key or not folder_id:
        # Provide a fallback response if credentials are missing
        response_placeholder.content = ""
        warning_message = "⚠️ Не настроены YandexCloud credentials. Использую демо-режим.\n\n"
        
        # Simple fallback response without API call
        if "время" in user_content.lower() or "time" in user_content.lower():
            from datetime import datetime, timezone
            current_time = datetime.now(timezone.utc).isoformat()
            warning_message += f"Текущее время (UTC): {current_time}"
        else:
            warning_message += f"Вы сказали: {user_content}\n\nДля полноценной работы настройте YANDEXCLOUD_API_KEY и YANDEXCLOUD_FOLDER_ID в .env файле."
        
        await response_placeholder.stream_token(warning_message)
        await response_placeholder.update()
    else:
        try:
            response = await provider.completions(
                messages=history, temperature=temperature, model=model
            )

            if response and response.text:
                # Clear the thinking indicator and update with actual response
                response_placeholder.content = ""

                # Stream the response token by token
                ai_response = response.text
                await response_placeholder.stream_token(ai_response)
                await response_placeholder.update()
            else:
                response_placeholder.content = ""
                error_message = "❌ Извините, мне не удалось сформировать ответ."
                await response_placeholder.stream_token(error_message)
                await response_placeholder.update()

        except Exception as e:
            response_placeholder.content = ""
            error_message = f"❌ Произошла ошибка: {str(e)}"
            await response_placeholder.stream_token(error_message)
            await response_placeholder.update()


@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates"""
    temperature = settings.get("temperature", 0.7)
    model = settings.get("model", "yandexgpt-lite/latest")

    await cl.Message(
        content=f"⚙️ Настройки обновлены:\n- Температура: {temperature}\n- Модель: {model}"
    ).send()


@cl.on_chat_end
async def on_chat_end():
    """Handle chat session end"""
    await stop_mcp_server()
    await cl.Message(content="👋 Спасибо за общение! До свидания!").send()


if __name__ == "__main__":
    # Run the Chainlit app
    cl.run()
