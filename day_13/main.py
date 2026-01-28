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
import time
from datetime import datetime

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


async def send_scheduled_messages():
    """Send scheduled messages every minute at 0 seconds"""
    while True:
        # Calculate seconds until next minute (0 seconds)
        now = datetime.now()
        seconds_until_next_minute = 60 - now.second
        
        # Wait until the next minute
        await asyncio.sleep(seconds_until_next_minute)
        
        # Get current time from MCP
        time_result = await call_mcp_tool("get_current_time")
        if time_result and time_result.content:
            time_text = time_result.content[0].text if hasattr(time_result.content[0], 'text') else str(time_result.content[0])
            
            # Generate message using YandexGPT directly
            message_prompt = f"Сформируй сообщение на русском языке в формате 'Московское время {time_text}.' где время должно быть написано прописью (словами), только время без даты. Ответ должен содержать только само сообщение без дополнительных пояснений."
            
            # Use YandexCloudProvider directly
            try:
                # Get the current settings
                settings = cl.user_session.get("chat_settings", {})
                model = settings.get("model", "yandexgpt-lite/latest")
                temperature = float(settings.get("temperature", 0.7))
                
                # Call YandexGPT through the provider
                completion_response = await provider.completions(
                    messages=[{"role": "user", "content": message_prompt}],
                    model=model,
                    temperature=temperature
                )
                
                if completion_response and completion_response.text:
                    message_text = completion_response.text
                    # Send the message to the chat
                    await cl.Message(content=message_text).send()
            except Exception as e:
                print(f"Error generating message: {e}")
                # Send error message to chat
                await cl.Message(content=f"Ошибка при генерации сообщения: {str(e)}").send()


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    print("Chat start called")
    
    # Start the scheduled message task
    cl.user_session.set("scheduled_task", asyncio.create_task(send_scheduled_messages()))
    
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
    initial_settings = {
        "temperature": "0.7",
        "model": "yandexgpt-lite/latest",
        "use_mcp": "Включено"
    }
    cl.user_session.set("chat_settings", initial_settings)
    
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
            Select(
                id="use_mcp",
                label="Использование MCP",
                values=["Включено", "Отключено"],
                initial="Включено",
            ),
        ]
    ).send()

    # Send welcome message
    await cl.Message(
        content="👋 Привет! Я готов к общению. Чем могу помочь?"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages - now ignoring them"""
    # Ignore user messages as per requirements
    pass


@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates"""
    temperature = settings.get("temperature", 0.7)
    model = settings.get("model", "yandexgpt-lite/latest")
    use_mcp = settings.get("use_mcp", "Включено")
    
    # Store settings in user session
    cl.user_session.set("chat_settings", settings)

    await cl.Message(
        content=f"⚙️ Настройки обновлены:\n- Температура: {temperature}\n- Модель: {model}\n- Использование MCP: {use_mcp}"
    ).send()


@cl.on_chat_end
async def on_chat_end():
    """Handle chat session end"""
    # Cancel the scheduled task if it exists
    scheduled_task = cl.user_session.get("scheduled_task")
    if scheduled_task and not scheduled_task.done():
        scheduled_task.cancel()
    
    await stop_mcp_server()
    await cl.Message(content="👋 Спасибо за общение! До свидания!").send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)