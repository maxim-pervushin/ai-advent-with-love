# AI Chat Application

A multi-provider AI chat application built with Python and Chainlit that supports OpenAI, Ollama, YandexCloud, and Gigachat.

## Features

- Support for multiple AI providers:
  - OpenAI (GPT models)
  - Ollama (Local LLMs)
  - YandexCloud
  - Gigachat
- Clean chat interface using Chainlit
- Easy provider switching
- REST API integration (no provider-specific libraries)

## Prerequisites

- Python 3.8+
- pip package manager
- API keys for the providers you want to use
- Ollama installed locally (for Ollama provider)

## Installation

### Quick Setup (Recommended)

#### On macOS/Linux:
```bash
./run.sh
```

#### On Windows:
```cmd
run.bat
```

### Manual Setup
1. Clone this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` to add your API keys for the providers you want to use

## Running the Application

```bash
chainlit run app.py -w
```

The application will be available at `http://localhost:8000`

## Testing API Connections

You can test your API connections with the provided test script:

```bash
python test_apis.py
```

## Usage

1. Select your preferred AI provider when starting a chat
2. Enter your API key if required by the provider (or use environment variables)
3. Start chatting!

## Provider Setup

### OpenAI
1. Get an API key from [OpenAI](https://platform.openai.com/)
2. Select "OpenAI" as your provider
3. Enter your API key when prompted or set `OPENAI_API_KEY` in your `.env` file

### Ollama
1. Install Ollama from [ollama.com](https://ollama.com/)
2. Pull a model (e.g., `ollama pull llama3.2`)
3. Start Ollama service
4. Select "Ollama" as your provider

### YandexCloud
1. Get an API key from [Yandex Cloud](https://cloud.yandex.com/)
2. Select "YandexCloud" as your provider
3. Enter your API key when prompted or set `YANDEXCLOUD_API_KEY` in your `.env` file
4. Update the model URI in your `.env` file with your folder ID

### Gigachat
1. Get an API key from [Sber](https://developers.sber.ru/)
2. Select "Gigachat" as your provider
3. Enter your API key when prompted or set `GIGACHAT_API_KEY` in your `.env` file

## Customization

You can modify the provider configurations in `app.py`:
- Change default models
- Update API endpoints
- Adjust request parameters

## Troubleshooting

- Ensure all required API keys are correctly entered
- Check that Ollama is running locally for Ollama provider
- Verify network connectivity to API endpoints
- Check provider-specific documentation for rate limits and quotas

## License

This project is licensed under the MIT License.