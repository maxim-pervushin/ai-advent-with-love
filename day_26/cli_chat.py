#!/usr/bin/env python3
"""
Command-line client for Ollama AI Service.
Uses the glm-4.7-flash:latest model.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import asyncio
import sys

from langchain_core.messages import HumanMessage, AIMessage

from ai_service.ollama_ai_service import OllamaAIService


async def interactive_chat():
    """Run an interactive chat session."""
    # Create AI service client
    ai_service = OllamaAIService("glm-4.7-flash:latest")
    
    try:
        # Initialize AI service
        await ai_service.initialize()
        
        print("\n" + "="*60)
        print("🤖 Ollama AI Service Client - Interactive Mode")
        print("="*60)
        print("\nCommands:")
        print("  /quit - Exit the program")
        print("  /help - Show this help message")
        print("="*60)
        
        chat_history = []
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                    
                if user_input.lower() in ['/help', 'help']:
                    print("\nCommands:")
                    print("  /quit - Exit the program")
                    print("  /help - Show this help message")
                    continue
                
                # Process the user's message
                response = await ai_service.chat(user_input, chat_history)
                print(f"\n🤖 Assistant: {response}")
                
                # Update chat history
                chat_history.append(HumanMessage(content=user_input))
                chat_history.append(AIMessage(content=response))
                
                # Keep history to a reasonable length
                if len(chat_history) > 10:
                    chat_history = chat_history[-10:]
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again.")
                
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        print("Please check that:")
        print("  1. Ollama is running (visit http://localhost:11434)")
        print("  2. The required model is available")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Single command mode
        message = " ".join(sys.argv[1:])
        print(f"Processing: {message}")
        # For single command mode, we would need to implement a non-interactive version
        print("Single command mode not yet implemented. Use interactive mode instead.")
        print("Run without arguments for interactive mode.")
    else:
        # Interactive mode
        asyncio.run(interactive_chat())


if __name__ == "__main__":
    main()