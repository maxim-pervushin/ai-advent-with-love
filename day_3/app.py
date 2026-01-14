from dataclasses import dataclass
import chainlit as cl
from chainlit.input_widget import Select
import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from providers.factory import ProviderFactory
from providers.base import Provider
from providers.config import SYSTEM_PROMPTS, PROVIDER_CONFIGS
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List

# Load environment variables
load_dotenv()

async def call_ai_provider(provider_name: str, messages: list, api_key: str = None, model: str = None) -> Optional[str]:
    """Call the appropriate AI provider based on selection"""

    # print(f"Calling {provider_name} API with messages:")
    # for message in messages:
        # print(message)

    try:
        # Create provider instance
        provider = ProviderFactory.create_provider(provider_name)
        
        # Call provider API
        return await provider.call_api(messages, api_key=api_key, model=model)
    except Exception as e:
        print(f"Error calling {provider_name} API: {e}")
        return None


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session with provider and model selection"""
    # Set initial message history
    cl.user_session.set("message_history", [])
    
    # Get available providers
    available_providers = ProviderFactory.get_available_providers()
    
    # Set YandexCloud as default provider
    default_provider = "YandexCloud"
    cl.user_session.set("provider", default_provider)
    
    # Set default model based on provider
    default_model = PROVIDER_CONFIGS[default_provider]["default_model"]
    cl.user_session.set("model", default_model)
    
    # Set default system prompt
    default_system_prompt = SYSTEM_PROMPTS[0]["name"]  # First prompt as default
    cl.user_session.set("system_prompt", default_system_prompt)
    
    # Create chat settings with provider and system prompt selection
    settings = await cl.ChatSettings(
        [
            Select(
                id="Provider",
                label="AI Provider",
                values=available_providers,
                initial_index=1,  # Ollama as default (index 1)
            ),
            Select(
                id="SystemPrompt",
                label="Answer Style",
                values=[prompt["name"] for prompt in SYSTEM_PROMPTS],
                initial_index=0,  # First prompt as default
            )
        ]
    ).send()
    
    # await cl.Message(content=f"Welcome! Using {default_provider} with model {default_model} and system prompt '{default_system_prompt}' by default. You can change provider, model, and system prompt in the settings. You can now start chatting!").send()


@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates"""
    # Update provider
    provider_name = settings["Provider"]
    cl.user_session.set("provider", provider_name)
    
    # Update model based on provider
    model = PROVIDER_CONFIGS[provider_name]["default_model"]
    cl.user_session.set("model", model)
    
    # Update system prompt
    system_prompt = settings["SystemPrompt"]
    cl.user_session.set("system_prompt", system_prompt)
    
    # Send confirmation message
    # await cl.Message(content=f"Settings updated: Using {provider_name} with model {model} and system prompt '{system_prompt}'").send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages"""
    # Get session data
    message_history = cl.user_session.get("message_history", [])
    provider = cl.user_session.get("provider", "YandexCloud")
    model = cl.user_session.get("model", PROVIDER_CONFIGS["YandexCloud"]["default_model"])
    api_key = cl.user_session.get("api_key", "")
    system_prompt_name = cl.user_session.get("system_prompt", SYSTEM_PROMPTS[0]["name"])
    
    # Find the selected system prompt
    selected_prompt_obj = next((prompt for prompt in SYSTEM_PROMPTS if prompt["name"] == system_prompt_name), SYSTEM_PROMPTS[0])
    selected_prompt = selected_prompt_obj["prompt"]
    selected_prompt_id = selected_prompt_obj["id"]

    if len(message_history) == 0:
        message_history.append({"role": "system", "content": selected_prompt})

    # Add user message to history
    user_message = {"role": "user", "content": message.content}
    message_history.append(user_message)
    
    # Create a placeholder for the AI response
    msg = cl.Message(content="")
    await msg.send()
    
    # Call the AI provider with the selected model and system prompt
    # messages = [
    #     {"role": "system", "content": selected_prompt},
    #     {"role": "user", "content": message.content}
    # ]
    ai_response = await call_ai_provider(provider, message_history, api_key, model)
    # ai_response = await call_ai_provider(provider, messages, api_key, model)
    
    if ai_response:
        # Update the message with the AI response
        msg.content = ai_response
        await msg.update()

        # parsed = []
        # if selected_prompt_id == 0:
        #     parsed = _parse_json(ai_response)
        # elif selected_prompt_id == 1:
        #     parsed = _parse_xml(ai_response)
        
        # print(f"{'-'*20}\n{parsed}\n{'-'*20}")
        # await cl.Message(content=f"Parsed response: {parsed}").send()
            
        # Add AI response to history
        message_history.append({"role": "assistant", "content": ai_response})
        cl.user_session.set("message_history", message_history)
    else:
        error_msg = "Sorry, I encountered an error while processing your request. Please try again."
        msg.content = error_msg
        await msg.update()