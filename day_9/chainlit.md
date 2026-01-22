# AI Chat with YandexCloud

Welcome to the AI Chat application powered by YandexCloud!

## Features

- Interactive chat with YandexCloud GPT models
- Conversation history tracking
- Token usage statistics
- Configurable settings

## Getting Started

1. Configure your `.env` file with YandexCloud credentials
2. Start chatting by typing your message below
3. View token usage and response time after each message

## Settings

You can customize the chat experience by modifying these environment variables in your `.env` file:

- `YANDEXCLOUD_MODEL` - Choose between: yandexgpt-lite/latest, yandexgpt/latest, yandexgpt-pro/latest
- `YANDEXCLOUD_TEMPERATURE` - Set creativity level (0.0-1.0)

## Tips

- Use lower temperature (0.0-0.3) for more focused, factual responses
- Use higher temperature (0.7-1.0) for more creative, varied responses
- The lite model is faster and more cost-effective for simple queries
- The pro model is best for complex tasks requiring detailed responses