import os
import asyncio
from typing import List, Dict, Any
import chainlit as cl
from chainlit.input_widget import TextInput, Select, Slider
from providers.yandexcloud import YandexCloudProvider
from dotenv import load_dotenv
import memory

# Load environment variables
load_dotenv()

# Initialize the YandexCloud provider
provider = YandexCloudProvider()


async def display_history(view_mode: str):
    """Display conversation history based on view mode"""
    if view_mode == "Полная история":
        messages = memory.get_full_history()
    else:
        messages = memory.get_ai_history()

    if not messages:
        await cl.Message(content="📝 История сообщений пуста.").send()
        return

    history_text = "📚 **История сообщений:**\n\n"

    for i, msg in enumerate(messages, 1):
        role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(
            msg["role"], "❓"
        )

        # Add summary indicator for full history view
        summary_indicator = (
            " 📋 *саммари*"
            if view_mode == "Полная история" and msg.get("is_summary", False)
            else ""
        )

        history_text += f"{i}. {role_emoji} **{msg['role'].title()}**{summary_indicator}:\n{msg['content']}\n\n"

    # Split into chunks if too long for Chainlit
    max_chunk_size = 4000
    if len(history_text) <= max_chunk_size:
        await cl.Message(content=history_text).send()
    else:
        # Split into chunks
        chunks = [
            history_text[i : i + max_chunk_size]
            for i in range(0, len(history_text), max_chunk_size)
        ]
        for i, chunk in enumerate(chunks):
            await cl.Message(
                content=f"**Часть {i + 1}/{len(chunks)}**\n\n{chunk}"
            ).send()


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    # Set initial settings
    settings = await cl.ChatSettings(
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
                id="history_view",
                label="Режим просмотра истории",
                values=["Полная история", "Как для AI (с саммари)"],
                initial="Полная история",
            ),
        ]
    ).send()

    message_count = memory.get_message_count()

    if message_count > 0:
        await display_history("Полная история")
        await cl.Message(
            content=f"📂 Возобновлён диалог с {message_count} сообщениями."
        ).send()
    else:
        # Send welcome message
        await cl.Message(
            content="👋 Привет! Я готов к общению. Чем могу помочь?"
        ).send()


async def summarize_conversation(history: List[Dict[str, str]]) -> str:
    """Summarize the recent conversation history and return a summary message"""
    # Create a prompt for summarization
    summarize_prompt = {
        "role": "user",
        "content": "Пожалуйста, предоставьте краткое резюме последних сообщений в нашем разговоре. Сосредоточьтесь на основных обсуждённых темах, принятых ключевых решениях и любой важной обменённой информации. Сделайте это кратко, но информативно.",
    }

    # Add the summarize prompt to the history
    messages_for_summary = history + [summarize_prompt]

    # Get settings from environment or use defaults
    temperature = float(os.getenv("YANDEXCLOUD_TEMPERATURE", "0.7"))
    model = os.getenv("YANDEXCLOUD_MODEL", "yandexgpt-lite/latest")

    try:
        # Call the YandexCloud API to get a summary
        response = await provider.completions(
            messages=messages_for_summary, temperature=temperature, model=model
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

    # Handle special commands for history display
    if user_content.strip() in ["/history", "/история"]:
        await display_history("Полная история")
        return

    if user_content.strip() in ["/ai_history", "/ai_история"]:
        await display_history("Как для AI (с саммари)")
        return

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

    # Get conversation history from database (AI gets summarized context)
    conversation_history = memory.get_ai_history()

    # Call the YandexCloud API
    try:
        response = await provider.completions(
            messages=conversation_history, temperature=temperature, model=model
        )

        if response and response.text:
            # Clear the thinking indicator and update with actual response
            response_placeholder.content = ""

            # Stream the response token by token (simulated)
            ai_response = response.text

            # Update the message with the full response
            await response_placeholder.stream_token(ai_response)

            # Store assistant response in database
            memory.add_message("assistant", ai_response)

            # Check if we need to summarize the conversation (every 10 messages since last summary)
            messages_since_summary = memory.get_messages_since_last_summary_count()
            if messages_since_summary >= 10:
                # Notify user that we're summarizing
                await cl.Message(
                    content="📝 Создаю саммари для сохранения контекста..."
                ).send()

                # Get messages since last summary for summarization
                messages_since_summary = memory.get_messages_since_summary()

                # Generate summary
                summary = await summarize_conversation(
                    [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in messages_since_summary
                    ]
                )

                # Add summary as system message (preserving full history)
                summary_content = f"Краткое содержание последних сообщений: {summary}"
                memory.add_summary(summary_content)

                # Notify user that summarization is complete
                await cl.Message(
                    content=f"✅ Создано саммари для контекста.\n{summary}"
                ).send()

            # Update the message with final content
            await response_placeholder.update()

        else:
            # Clear the thinking indicator and show error message
            response_placeholder.content = ""
            error_message = "❌ Извините, мне не удалось сформировать ответ. Пожалуйста, попробуйте снова."
            await response_placeholder.stream_token(error_message)
            await response_placeholder.update()

    except Exception as e:
        # Clear the thinking indicator and show error message
        response_placeholder.content = ""
        error_message = f"❌ Произошла ошибка: {str(e)}"
        await response_placeholder.stream_token(error_message)
        await response_placeholder.update()


@cl.on_settings_update
async def on_settings_update(settings: Dict[str, Any]):
    """Handle settings updates"""
    temperature = settings.get("temperature", 0.7)
    model = settings.get("model", "yandexgpt-lite/latest")
    history_view = settings.get("history_view", "Полная история")

    # Display history based on the selected view mode
    await display_history(history_view)

    await cl.Message(
        content=f"⚙️ Настройки обновлены:\n- Температура: {temperature}\n- Модель: {model}\n- Режим истории: {history_view}"
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
