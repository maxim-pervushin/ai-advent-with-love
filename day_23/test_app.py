"""Test script for Educational Platform Support Assistant"""

from providers import OllamaProvider
from rag_engine import RAGEngine
from crm_integration import CRMIntegration


def test_full_integration():
    """Test the full integration of all components"""
    print("Testing Educational Platform Support Assistant components...")
    
    # Test RAG Engine
    print("\n1. Testing RAG Engine...")
    rag = RAGEngine()
    context = rag.get_context_string("Проблемы с авторизацией")
    print(f"   RAG context length: {len(context)} characters")
    print(f"   Context preview: {context[:200]}...")
    
    # Test CRM Integration
    print("\n2. Testing CRM Integration...")
    crm = CRMIntegration()
    ticket = crm.get_ticket("ticket_001")
    print(f"   Ticket subject: {ticket['subject']}")
    
    user = crm.get_user(ticket["user_id"])
    print(f"   User name: {user['name']}")
    
    ticket_context = crm.get_ticket_context("ticket_001")
    print(f"   Ticket context length: {len(ticket_context)} characters")
    print(f"   Ticket context preview: {ticket_context[:100]}...")
    
    # Test LLM Provider
    print("\n3. Testing LLM Provider...")
    llm = OllamaProvider()
    
    # Create a prompt combining all context
    prompt = f"""Вы - помощник технической поддержки образовательной платформы.
    
Контекст тикета:
{ticket_context}

Информация из документации:
{context}

Пожалуйста, дайте полезный ответ на русском языке по теме: Проблемы с авторизацией"""

    response = llm.generate(prompt)
    print(f"   LLM response length: {len(response)} characters")
    print(f"   Response preview: {response[:300]}...")
    
    print("\nAll components tested successfully!")


if __name__ == "__main__":
    test_full_integration()