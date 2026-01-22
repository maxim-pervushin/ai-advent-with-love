#!/bin/bash

# AI Chat with YandexCloud - Run Script

echo "🚀 Starting AI Chat with YandexCloud..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please copy .env.example to .env and add your YandexCloud credentials:"
    echo "  cp .env.example .env"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Check if dependencies are installed
if ! python -c "import chainlit" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Start the Chainlit application
echo "🤖 Starting Chainlit application..."
echo "Open your browser to: http://localhost:8000"
echo ""
chainlit run main.py -w