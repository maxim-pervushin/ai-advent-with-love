"""
Test script for AI provider APIs
"""
import os
import asyncio
from dotenv import load_dotenv
from providers.factory import ProviderFactory
from providers.base import Provider

# Load environment variables
load_dotenv()

async def test_provider(provider_name: str) -> bool:
    """Test a provider API"""
    try:
        # Create provider instance
        provider1 = ProviderFactory.create_provider(provider_name)
        provider2 = ProviderFactory.create_provider(provider_name)
        
        # Check if the same instance is returned (caching test)
        is_cached = provider1 is provider2
        print(f"{provider_name} caching test: {'PASSED' if is_cached else 'FAILED'}")
        
        # Test messages
        messages = [{"role": "user", "content": "Hello, this is a test!"}]
        
        # Call provider API
        response = await provider1.call_api(messages)
        
        if response:
            print(f"{provider_name} API test successful: {response}")
            return True
        else:
            print(f"{provider_name} API test failed: No response")
            return False
    except Exception as e:
        print(f"Error testing {provider_name} API: {e}")
        return False



if __name__ == "__main__":
    print("Testing AI Provider APIs...")
    print("=" * 40)
    
    async def run_tests():
        tests = [
            # ("OpenAI", lambda: test_provider("OpenAI")),
            # ("Ollama", lambda: test_provider("Ollama")),
            # ("OllamaCloud", lambda: test_provider("OllamaCloud")),
            # ("YandexCloud", lambda: test_provider("YandexCloud")),
            # ("Gigachat", lambda: test_provider("Gigachat")),
            ("OpenRouter", lambda: test_provider("OpenRouter"))
        ]
        
        for name, test_func in tests:
            print(f"\nTesting {name}...")
            try:
                success = await test_func()
                if success:
                    print(f"✓ {name} test passed")
                else:
                    print(f"✗ {name} test failed")
            except Exception as e:
                print(f"✗ {name} test error: {e}")
    
    # Run the async tests
    asyncio.run(run_tests())
    
    print("\n" + "=" * 40)
    print("API testing complete!")