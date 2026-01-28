# AI Chat with YandexCloud

A modern chat application built with Chainlit and YandexCloud's GPT models.

## Features

- 🤖 Interactive chat interface powered by YandexCloud GPT
- 💬 Conversation history tracking
- 📊 Token usage statistics
- ⚙️ Configurable model and temperature settings
- 🔄 Chat session resumption support

## Prerequisites

- Python 3.8 or higher
- YandexCloud account with API access
- API Key and Folder ID from YandexCloud

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit the `.env` file and add your YandexCloud credentials:

```env
YANDEXCLOUD_API_KEY=your_actual_api_key_here
YANDEXCLOUD_FOLDER_ID=your_actual_folder_id_here
YANDEXCLOUD_MODEL=yandexgpt-lite/latest
YANDEXCLOUD_TEMPERATURE=0.7
```

### Getting YandexCloud Credentials

1. Go to [YandexCloud Console](https://console.cloud.yandex.com/)
2. Create a service account or use your existing account
3. Generate an API key in the IAM section
4. Note your Folder ID from the console

## Usage

### Start the Application

```bash
chainlit run main.py -w
```

The `-w` flag enables auto-reload during development.

### Available Models

- `yandexgpt-lite/latest` - Fast, cost-effective model
- `yandexgpt/latest` - Balanced performance
- `yandexgpt-pro/latest` - Most capable model

### Temperature Settings

- `0.0 - 0.3` - More focused, deterministic responses
- `0.4 - 0.7` - Balanced creativity and focus (recommended)
- `0.8 - 1.0` - More creative, varied responses

## Project Structure

```
.
├── main.py                      # Chainlit application
├── providers/
│   ├── __init__.py
│   ├── base.py                  # Base provider interface
│   ├── completion_response.py   # Response dataclass
│   ├── factory.py               # Provider factory
│   └── yandexcloud.py           # YandexCloud provider implementation
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## Features Explained

### Conversation History
The application maintains a conversation history throughout the session, allowing for context-aware responses.

### Token Usage
After each response, you'll see token usage statistics:
- Total tokens used
- Prompt tokens (input)
- Completion tokens (output)
- Response latency

### Settings
You can adjust the model and temperature settings in the `.env` file:
- `YANDEXCLOUD_MODEL` - Which model to use
- `YANDEXCLOUD_TEMPERATURE` - Creativity level (0.0-1.0)

## Troubleshooting

### API Key Issues
If you receive authentication errors:
- Verify your API key is correct
- Ensure your service account has proper permissions
- Check that your folder ID is accurate

### Connection Issues
If the app can't connect to YandexCloud:
- Check your internet connection
- Verify the API endpoint is accessible
- Ensure your firewall allows outbound connections

### Model Not Found
If you get a model not found error:
- Verify the model name is correct
- Check if the model is available in your region
- Try using a different model (e.g., `yandexgpt-lite/latest`)

## Development

### Adding New Providers

To add a new AI provider:

1. Create a new provider file in `providers/` directory
2. Inherit from the `Provider` base class
3. Implement the `completions` and `tokenize` methods
4. Import and use the provider in `main.py`

Example:

```python
from providers.yandexcloud import YandexCloudProvider

provider = YandexCloudProvider()
response = await provider.completions(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    model="yandexgpt-lite/latest"
)
```

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
- Check the [YandexCloud Documentation](https://cloud.yandex.com/en/docs/)
- Review the [Chainlit Documentation](https://docs.chainlit.io/)