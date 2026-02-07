import chainlit as cl
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchText
import ollama
from providers.ollama import OllamaProvider
from history_store import HistoryStore

HISTORY_SUMMARY_THRESHOLD = 10
COLLECTION_NAME = "pdf_documents"
EMBEDDING_MODEL = "evilfreelancer/enbeddrus:latest"
LLM_MODEL = "qwen3:8b"

ollama_provider = OllamaProvider()
history_store = HistoryStore()


def get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client"""
    return QdrantClient(url="http://localhost:6333")


def search_qdrant(query: str, limit: int = 5) -> List[Dict]:
    """Search Qdrant for relevant documents"""
    try:
        client = get_qdrant_client()
        query_embedding = ollama.embed(model=EMBEDDING_MODEL, input=[query])[
            "embeddings"
        ][0]

        results = client.search(
            collection_name=COLLECTION_NAME, query_vector=query_embedding, limit=limit
        )

        return [
            {
                "content": hit.payload.get("content", ""),
                "score": hit.score,
                "source": hit.payload.get("source", "unknown"),
            }
            for hit in results
        ]
    except Exception as e:
        print(f"Error searching Qdrant: {e}")
        return []


def get_rag_context(query: str, limit: int = 5) -> str:
    """Get RAG context from Qdrant"""
    results = search_qdrant(query, limit)
    if not results:
        return ""

    context_parts = []
    for i, result in enumerate(results):
        context_parts.append(
            f"[Document {i + 1}] (Source: {result['source']})\n{result['content']}"
        )

    return "\n\n".join(context_parts)


async def generate_summary(messages: List[Dict[str, str]]) -> str:
    """Generate a summary of the chat history"""
    try:
        system_prompt = """You are a helpful assistant that summarizes chat conversations. Provide a concise but comprehensive summary of the key points discussed. Keep the summary under 200 words."""

        all_messages = [{"role": "system", "content": system_prompt}] + messages

        response = await ollama_provider.completions(
            messages=all_messages, temperature=0.3, model=LLM_MODEL
        )

        if response:
            return response.text
        return "Error generating summary."
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Error generating summary."


async def get_ai_response(
    messages: List[Dict[str, str]], use_rag: bool = True, user_query: str = ""
) -> str:
    """Get AI response using chat history and optionally RAG"""
    try:
        rag_context = ""
        if use_rag:
            rag_context = get_rag_context(user_query)

        system_message = """You are a helpful AI assistant. Answer the user's questions based on the chat history and any relevant context provided."""

        if rag_context:
            system_message += f"""

Relevant context from documents:
{rag_context}

Use this context to answer the user's question if it relates to the documents. Otherwise, rely on the chat history and your general knowledge.
"""

        all_messages = [{"role": "system", "content": system_message}] + messages

        response = await ollama_provider.completions(
            messages=all_messages, temperature=0.7, model=LLM_MODEL
        )

        if response:
            return response.text
        return "Error: No response from AI."
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return f"Error: {str(e)}"


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session"""
    await cl.Message(
        content="Hello! I'm your AI assistant. I can answer your questions using chat history and documents from the RAG system."
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages"""
    user_content = message.content

    history_store.add_message("user", user_content)

    messages = history_store.get_all_messages()

    msg = cl.Message(content="")
    await msg.send()

    ai_response = await get_ai_response(messages, use_rag=True, user_query=user_content)

    await msg.stream_token(ai_response)

    history_store.add_message("assistant", ai_response)

    message_count = history_store.get_message_count()
    if message_count > HISTORY_SUMMARY_THRESHOLD:
        try:
            summary = await generate_summary(messages)
            recent_messages = messages[-5:]
            history_store.update_messages_with_summary(summary, recent_messages)
            summary_msg = cl.Message(
                content=f"\n\n[Summarized {message_count - 5} previous messages]"
            )
            await summary_msg.send()
        except Exception as e:
            print(f"Error during summarization: {e}")


@cl.on_chat_end
async def on_chat_end():
    """Clean up on chat end"""
    pass
