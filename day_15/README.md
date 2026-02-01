# AI-Assisted Programming CLI

A command-line utility for AI-assisted programming with MCP (Model Context Protocol) support.

## Features

- **Command-line dialog UI** - Interactive chat interface for requesting code
- **MCP Tools** - File operations and shell execution in the `out` subfolder
- **Multiple AI providers** - Support for OpenRouter, YandexCloud, GigaChat, Mistral, and Ollama
- **Multi-file generation** - Create multiple files in a single request

## Quick Start

### 1. Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the CLI

```bash
# Using default provider (OpenRouter)
python3 cli.py

# Using specific provider
python3 cli.py --provider yandexcloud
python3 cli.py --provider gigachat
python3 cli.py --provider mistral
python3 cli.py --provider ollama
```

### 3. Example Usage

```
You: Make a quick sort in python
Assistant: Done. Saved to ./out/quick_sort.py
```

```
You: Make a server with FastAPI. Prepare for Docker
Assistant: Done. Saved to ./out/requirements.txt
Assistant: Done. Saved to ./out/server.py
Assistant: Done. Saved to ./out/Dockerfile
Assistant: Done. Saved to ./out/docker-compose.yml
```

## Files

- `cli.py` - Main CLI application with chat interface
- `mcp_server.py` - MCP server providing file and shell tools
- `test_demo.py` - Demonstration script testing all features

## MCP Tools Available

| Tool | Description |
|------|-------------|
| `write_file` | Write content to a file in `out/` subfolder |
| `read_file` | Read content from a file in `out/` subfolder |
| `list_files` | List files in `out/` subfolder |
| `execute_shell` | Execute shell commands in `out/` directory |

## Requirements

- Python 3.10+
- AI provider API keys configured in `.env`

## Configuration

Configure your AI provider API keys in `.env`:

```env
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free

YANDEXCLOUD_API_KEY=your_key
YANDEXCLOUD_FOLDER_ID=your_folder_id
YANDEXCLOUD_MODEL=aliceai-llm/latest

GIGACHAT_API_KEY=your_key
GIGACHAT_MODEL=GigaChat-2

MISTRAL_API_KEY=your_key
MISTRAL_MODEL=mistral-tiny
```

## Testing

Run the demonstration:

```bash
source venv/bin/activate
python3 test_demo.py
```

This will:
1. Create a quick sort implementation
2. List files in the `out/` folder
3. Execute the script to verify it works
4. Create a complete FastAPI server with Docker setup
5. Show all created files
