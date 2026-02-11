"""Educational Platform Support Assistant using Chainlit"""

import chainlit as cl
from providers import YandexProvider
from rag_engine import RAGEngine
from crm_integration import CRMIntegration
import re


# Initialize components
rag_engine = RAGEngine()
crm = CRMIntegration()
llm = YandexProvider()


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat with a welcome message"""
    welcome_message = """Здравствуйте! Я ваш помощник по образовательной платформе. 
Я могу помочь вам с вопросами по курсам, техническими проблемами, вопросами оплаты и другим темам.

Если у вас есть открытый тикет в поддержке, просто упомяните его номер (например, "ticket_001"), 
и я смогу учитывать контекст вашего обращения при ответе.

Чем могу вам помочь?"""
    
    await cl.Message(content=welcome_message).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Process incoming messages and generate responses"""
    user_message = message.content
    
    # Check if user is referencing a ticket
    ticket_id = extract_ticket_id(user_message)
    
    # Get relevant context from documentation
    doc_context = rag_engine.get_context_string(user_message)
    
    # Get ticket context if ticket ID is mentioned
    ticket_context = ""
    if ticket_id:
        ticket_context = crm.get_ticket_context(ticket_id)
    
    # Prepare the prompt for the LLM
    prompt = create_prompt(user_message, doc_context, ticket_context)
    
    # Generate response using LLM
    response = llm.generate(prompt)
    
    # Send response to user
    await cl.Message(content=response).send()


def extract_ticket_id(message: str) -> str:
    """Extract ticket ID from message if present"""
    match = re.search(r"(ticket_\d+)", message, re.IGNORECASE)
    return match.group(1) if match else ""


def create_prompt(user_message: str, doc_context: str, ticket_context: str) -> str:
    """Create a prompt for the LLM with all relevant context"""
    prompt = "Вы - помощник технической поддержки образовательной платформы. "
    prompt += "Ваша задача - помогать пользователям с вопросами по платформе, курсам и другим аспектам обучения.\n\n"
    
    if ticket_context:
        prompt += "Контекст тикета поддержки:\n"
        prompt += ticket_context + "\n\n"
    
    if doc_context:
        prompt += "Информация из документации платформы:\n"
        prompt += doc_context + "\n\n"
    
    prompt += "Вопрос пользователя:\n"
    prompt += user_message + "\n\n"
    prompt += "Пожалуйста, дайте полезный и точный ответ на русском языке, используя предоставленную информацию. "
    prompt += "Если вопрос касается конкретного тикета, учитывайте его контекст. "
    prompt += "Если в документации нет точной информации, дайте общий полезный ответ. "
    prompt += "Если вопрос касается технической проблемы, предложите пошаговое решение."
    
    return prompt


if __name__ == "__main__":
    # For testing purposes
    print("Educational Platform Support Assistant")
    print("This app should be run with: chainlit run app.py")