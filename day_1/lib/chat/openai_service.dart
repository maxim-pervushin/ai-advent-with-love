import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_config.dart';

class OpenAIService {
  // static const String _baseUrl = 'https://api.openai.com/v1';
  static const String _baseUrl = 'https://llm.api.cloud.yandex.net/v1';
  Future<String> getChatResponse(List<Map<String, dynamic>> messages) async {
    try {
      final folderId = 'b1g83j7vllo66acelt7v';
      final response = await http.post(
        Uri.parse('$_baseUrl/chat/completions'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${ApiConfig.openAiApiKey}',
          'OpenAI-Project': folderId
        },
        body: jsonEncode({
          // 'model': 'gpt-4o-mini',
          'model': "gpt://$folderId/yandexgpt-lite/latest",
          'messages': messages,
          'temperature': 0.7,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['choices'][0]['message']['content'];
      } else {
        throw Exception('Failed to get response: ${response.statusCode} ${response.body}');
      }
    } catch (e) {
      throw Exception('Error calling OpenAI API: $e');
    }
  }
}