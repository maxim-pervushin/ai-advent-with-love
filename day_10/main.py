import os
import asyncio
from typing import List, Dict, Any
import chainlit as cl
from providers.yandexcloud import YandexCloudProvider
from dotenv import load_dotenv
import memory

# Load environment variables
load_dotenv()

# Initialize the YandexCloud provider
provider = YandexCloudProvider()


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    message_count = memory.get_message_count()
    
    if message_count > 0:
        await cl.Message(
            content=f"📂 Возобновлён диалог с {message_count} сообщениями."
        ).send()
    else:
        # Send welcome message
        await cl.Message(content="👋 Привет! Я готов к общению. Чем могу помочь?").send()


async def summarize_conversation(history: List[Dict[str, str]]) -> str:
    """Summarize the conversation history and return a summary message"""
    # Create a prompt for summarization
    summarize_prompt = {
        "role": "user",
        "content": "Пожалуйста, предоставьте краткое резюме нашего разговора на данный момент. Сосредоточьтесь на основных обсуждённых темах, принятых ключевых решениях и любой важной обменённой информации. Сделайте это кратко, но информативно."
    }
    
    # Add the summarize prompt to the history
    messages_for_summary = history + [summarize_prompt]
    
    # Get settings from environment or use defaults
    temperature = float(os.getenv("YANDEXCLOUD_TEMPERATURE", "0.7"))
    model = os.getenv("YANDEXCLOUD_MODEL", "yandexgpt-lite/latest")
    
    try:
        # Call the YandexCloud API to get a summary
        response = await provider.completions(
            messages=messages_for_summary,
            temperature=temperature,
            model=model
        )
        
        if response and response.text:
            return response.text
        else:
            return "Саммари беседы не удалось сформировать."
    except Exception as e:
        return f"Ошибка при генерации саммари: {str(e)}"


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages"""
    
    # Get message content
    user_content = message.content
    
    # Store user message in database
    memory.add_message("user", user_content)
    
    # Create a placeholder for the AI response
    response_placeholder = cl.Message(content="")
    await response_placeholder.send()
    
    # Get settings from environment or use defaults
    temperature = float(os.getenv("YANDEXCLOUD_TEMPERATURE", "0.7"))
    model = os.getenv("YANDEXCLOUD_MODEL", "yandexgpt-lite/latest")
    
    # Show typing indicator
    await response_placeholder.stream_token("🤔 Думаю...")
    
    # Get conversation history from database
    conversation_history = memory.get_conversation_history()
    
    # Call the YandexCloud API
    try:
        response = await provider.completions(
            messages=conversation_history,
            temperature=temperature,
            model=model
        )
        
        if response and response.text:
            # Clear the thinking indicator
            await response_placeholder.stream_token("\n\n")
            
            # Stream the response token by token (simulated)
            ai_response = response.text
            
            # Update the message with the full response
            await response_placeholder.stream_token(ai_response)
            
            # Store assistant response in database
            memory.add_message("assistant", ai_response)
            
            # Check if we need to summarize the conversation (every 10 messages)
            message_count = memory.get_message_count()
            if message_count >= 10:
                # Notify user that we're summarizing
                await cl.Message(content="📝 Суммирую беседу, чтобы сохранить контекст...").send()
                
                # Get current history for summarization
                current_history = memory.get_conversation_history()
                
                # Generate summary
                summary = await summarize_conversation(current_history)
                
                # Clear old messages and add summary as system message
                memory.clear_history()
                memory.add_message("system", f"Краткое содержание предыдущего разговора: {summary}")
                
                # Notify user that summarization is complete
                await cl.Message(content=f"✅ Разговор был обобщён, контекст сброшен.\n{summary}").send()
            
            # Update the message with final content
            await response_placeholder.update()
            
        else:
            error_message = "❌ Извините, мне не удалось сформировать ответ. Пожалуйста, попробуйте снова."
            await response_placeholder.stream_token(error_message)
            await response_placeholder.update()
            
    except Exception as e:
        error_message = f"❌ Произошла ошибка: {str(e)}"
        await response_placeholder.stream_token(error_message)
        await response_placeholder.update()


@cl.on_settings_update
async def on_settings_update(settings: Dict[str, Any]):
    """Handle settings updates"""
    temperature = settings.get("temperature", 0.7)
    model = settings.get("model", "yandexgpt-lite/latest")
    
    await cl.Message(
        content=f"⚙️ Настройки обновлены:\n- Температура: {temperature}\n- Модель: {model}"
    ).send()


@cl.on_chat_resume
async def on_chat_resume(thread: Dict[str, Any]):
    """Resume a previous chat session"""
    message_count = memory.get_message_count()
    await cl.Message(
        content=f"📂 Возобновлён диалог с {message_count} сообщениями."
    ).send()


@cl.on_chat_end
async def on_chat_end():
    """Handle chat session end"""
    await cl.Message(content="👋 Спасибо за общение! До свидания!").send()


if __name__ == "__main__":
    # Run the Chainlit app
    cl.run()