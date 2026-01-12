# Chat with AI

A Flutter application that allows you to chat with an AI assistant powered by OpenAI's GPT models.

## Features

- Real-time chat interface with AI assistant
- Message history display
- Responsive UI with message bubbles
- Loading indicators during AI processing

## Getting Started

### Prerequisites

- Flutter SDK installed
- An OpenAI API key

### Setup

1. Clone the repository
2. Run `flutter pub get` to install dependencies
3. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```
4. Run the app with `flutter run`

## Usage

1. Type your message in the input field at the bottom
2. Press Send or hit Enter to submit your message
3. Wait for the AI assistant to respond
4. Continue the conversation!

## Dependencies

- `http`: For making API calls to OpenAI
- `flutter_dotenv`: For loading environment variables

## Architecture

The app follows a simple structure:
- `main.dart`: Entry point of the application
- `chat/chat_screen.dart`: The main chat interface
- `chat/chat_message.dart`: Data model for chat messages
- `chat/openai_service.dart`: Service for communicating with OpenAI API

## Contributing

Feel free to fork the project and submit pull requests for improvements.
