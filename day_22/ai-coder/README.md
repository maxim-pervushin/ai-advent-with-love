# AI Coder - Command-Line Programming Assistant

A CLI tool that uses Ollama's local AI model to help programmers with coding tasks.

## Prerequisites

1. **Ollama** - Install from https://ollama.com
2. **Python 3.8+**
3. **Git** (optional, for commit message generation)

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull the model (adjust model name as needed)
ollama pull llama3.2
```

## Configuration

### Ollama (default)

```bash
export OLLAMA_HOST="http://localhost:11434"  # Ollama server address
export OLLAMA_MODEL="llama3.2"               # Model to use
```

### Yandex Cloud

```bash
export YANDEX_FOLDER_ID="your-folder-id"     # Yandex Cloud folder ID
export YANDEX_API_KEY="your-api-key"         # Yandex Cloud API key
export YANDEX_ENDPOINT="https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
```

To switch providers, edit `ai_coder.py` and change the import:

```python
# For Ollama:
from providers.ollama_provider import OllamaProvider

# For Yandex:
from providers.yandex_provider import YandexProvider
```

## Usage

```bash
python ai_coder.py
```

### Commands

| Command | Description |
|---------|-------------|
| `/open PATH` | Select working directory (all operations restricted here) |
| `/ls` | List files in current directory |
| `/make PROMPT` | Create/update files based on your request |
| `/help QUESTION` | Ask questions about your code |
| `/commit` | Generate git commit message from changes |
| `/exit` | Exit the program |

### Examples

**Open a project:**
```
AI Coder> /open /path/to/my/project
```

**Create a minesweeper game:**
```
AI Coder> /make Create a minesweeper game with HTML, CSS, and JavaScript
```

**Ask about API endpoints:**
```
AI Coder> /help List all API endpoints in the codebase
```

**Generate a commit message:**
```
AI Coder> /commit
```

## Security

- All file operations are restricted to the selected directory
- Paths outside the selected directory are blocked
- Git operations use the current working directory context
