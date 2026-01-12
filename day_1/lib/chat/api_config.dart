import 'package:flutter_dotenv/flutter_dotenv.dart';

class ApiConfig {
  static String get openAiApiKey {
    final key = dotenv.env['OPENAI_API_KEY'];
    if (key == null || key.isEmpty) {
      throw Exception('OPENAI_API_KEY is not set in .env file');
    }
    return key;
  }
}