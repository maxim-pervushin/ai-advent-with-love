import os
import asyncio
import chainlit as cl
from providers.yandexcloud import YandexCloudProvider
from dotenv import load_dotenv
import subprocess
import sys
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
import time
from datetime import datetime
import re

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
            
            # Get available MCP tools
            tools_response = await get_mcp_tools()
            
            # Format tools message
            tools_info = "\n\n📋 **Доступные MCP инструменты:**\n"
            if tools_response and hasattr(tools_response, 'tools'):
                for tool in tools_response.tools:
                    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                    tool_desc = tool.description if hasattr(tool, 'description') else "Нет описания"
                    tools_info += f"\n- **{tool_name}**: {tool_desc}"
            else:
                tools_info += "\nНе удалось получить список инструментов"
            
            await cl.Message(content=f"🟢 MCP сервер запущен{tools_info}").send()
        else:
            print("MCP Server failed to start")
            await cl.Message(content="⚠️ MCP сервер не запущен").send()
    except Exception as e:
        print(f"MCP Server Error: {e}")
        import traceback
        traceback.print_exc()
        await cl.Message(content=f"⚠️ MCP сервер не запущен: {str(e)}").send()
    
    # Send welcome message with instructions
    welcome_message = """👋 Привет! Я готов к общению. Чем могу помочь?

**Возможности:**
- 📝 Обычный чат с ИИ на русском языке
- 🔗 Обработка URL-адресов: отправьте URL, и я получу содержимое, создам краткое содержание и сохраню его в файл MD

**Примеры:**
- "Расскажи о...")
- "https://example.com/article" - я обработаю эту ссылку и сохраню краткое содержание"""
    
    await cl.Message(content=welcome_message).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages"""
    # Check if message contains a URL
    url = extract_url(message.content)
    if url:
        # Process URL
        await process_url_message(url, message)
        return
    
    # For non-URL messages, use the standard response
    await process_standard_message(message)


@cl.on_chat_end
async def on_chat_end():
    """Handle chat session end"""
    
    await stop_mcp_server()
    await cl.Message(content="👋 Спасибо за общение! До свидания!").send()


def extract_url(text):
    """Extract the first URL from text"""
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None


async def process_url_message(url, message):
    """Process a message containing a URL"""
    # Send a message indicating we're processing the URL
    await cl.Message(content=f"Обрабатываю URL: {url}").send()
    
    # Fetch content using MCP tool
    content_result = await call_mcp_tool("fetch_content", {"url": url})
    
    if content_result and hasattr(content_result, 'content') and content_result.content:
        # Extract text and title from content
        content_data = content_result.content[0].text if hasattr(content_result.content[0], 'text') else str(content_result.content[0])
        
        # Parse the content data (it's now a JSON string)
        import json
        try:
            content_dict = json.loads(content_data)
            content_text = content_dict.get("content", "")
            title = content_dict.get("title", None)
        except json.JSONDecodeError:
            # Fallback if it's not JSON
            content_text = content_data
            title = None
        
        # Check if there was an error fetching content
        if content_text.startswith("Error"):
            await cl.Message(content=f"Ошибка при получении содержимого: {content_text}").send()
            return
        
        # Generate summary using YandexGPT
        summary = await generate_summary(content_text, url)
        
        # Use the title from the content if available, otherwise extract from content or URL
        if title:
            filename_title = title
        else:
            filename_title = extract_title_from_content(content_text, url)
        
        # Clean title for filename
        filename_title = re.sub(r'[^\w\s-]', '', filename_title).strip()
        filename_title = re.sub(r'[-\s]+', '-', filename_title)  # Replace spaces/hyphens with single hyphen
        filename_title = filename_title[:50]  # Limit length
        
        # Save summary to file using MCP tool
        filename = f"{filename_title}.md"
        write_result = await call_mcp_tool("write_file", {
            "content": summary,
            "filename": filename
        })
        
        if write_result and hasattr(write_result, 'content') and write_result.content:
            result_text = write_result.content[0].text if hasattr(write_result.content[0], 'text') else str(write_result.content[0])
            if not result_text.startswith("Error"):
                await cl.Message(content=f"Содержимое сохранено в файл: {filename}").send()
            else:
                await cl.Message(content=f"Ошибка при сохранении файла: {result_text}").send()
        else:
            await cl.Message(content="Ошибка при сохранении файла").send()
    else:
        await cl.Message(content="Не удалось получить содержимое URL").send()

async def process_standard_message(message):
    """Process standard messages (non-URL)"""
    # Use default values
    model = "yandexgpt-lite/latest"
    temperature = 0.7
    
    
    # System instructions for AI
    system_instructions = """Вы - умный помощник с возможностью обработки веб-контента. При работе с сообщениями следуйте этим правилам:

1. Если сообщение содержит URL:
   - Используйте MCP инструмент fetch_content для получения содержимого
   - При успешном получении содержимого создайте краткое содержание (суммаризацию)
   - Сохраните краткое содержание в MD файл с помощью MCP инструмента write_file
   - Имя файла должно быть основано на заголовке содержимого
   - Сообщите пользователю о результате операции

2. Если сообщение не содержит URL:
   - Обрабатывайте сообщение как обычный запрос
   - Отвечайте на русском языке
   - Будьте вежливы и полезны

3. Форматирование MD файла:
   - Используйте заголовок на основе заголовка страницы
   - Добавьте краткое содержание
   - Включите исходный URL
   - Используйте Markdown для форматирования"""
    
    # Prepare messages for the provider
    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": message.content}
    ]
    
    # Call the provider
    try:
        completion_response = await provider.completions(
            messages=messages,
            model=model,
            temperature=temperature
        )
        
        if completion_response and completion_response.text:
            # Send the response
            await cl.Message(content=completion_response.text).send()
        else:
            await cl.Message(content="Не удалось получить ответ").send()
    except Exception as e:
        print(f"Error generating response: {e}")
        await cl.Message(content=f"Ошибка при генерации ответа: {str(e)}").send()


async def generate_summary(content, url):
    """Generate a summary of the content using YandexGPT"""
    # Truncate content if too long
    max_length = 5000
    if len(content) > max_length:
        content = content[:max_length] + "..."
    
    summary_prompt = f"""Вы должны создать краткое и информативное содержание следующего текста на русском языке.

Текст взят с URL: {url}

Требования к краткому содержанию:
- Пишите на русском языке
- Выделите основные идеи и ключевые моменты
- Сохраняйте важные факты и цифры
- Используйте четкую и лаконичную структуру
- Длина краткого содержания должна быть 3-5 абзацев

Текст:
{content}

Краткое содержание:"""
    
    try:
        # Use default values
        model = "yandexgpt-lite/latest"
        temperature = 0.7
        
        # Call YandexGPT through the provider
        completion_response = await provider.completions(
            messages=[{"role": "user", "content": summary_prompt}],
            model=model,
            temperature=temperature
        )
        
        if completion_response and completion_response.text:
            return completion_response.text
        else:
            return "Не удалось создать краткое содержание."
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"Ошибка при создании краткое содержания: {str(e)}"


def extract_title_from_content(content, url):
    """Extract a title from content or URL for filename"""
    # Try to find a title in the content (look for title tags or first heading)
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
    else:
        # Try to find first heading
        heading_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
        if heading_match:
            title = heading_match.group(1).strip()
        else:
            # Use URL as fallback
            title = url.split('/')[-1] or url.replace('http://', '').replace('https://', '').split('/')[0]
    
    # Clean title for filename
    title = re.sub(r'[^\w\s-]', '', title).strip()
    title = re.sub(r'[-\s]+', '-', title)  # Replace spaces/hyphens with single hyphen
    return title[:50]  # Limit length


if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)