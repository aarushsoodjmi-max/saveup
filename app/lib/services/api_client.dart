import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../core/constants/api_constants.dart';
import 'token_storage.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiClient {
  static final ApiClient _instance = ApiClient._();
  factory ApiClient() => _instance;
  ApiClient._();

  final _client = http.Client();

  // ── Internal helpers ──────────────────────────────────────────────────────

  Future<Map<String, String>> _headers({bool auth = true}) async {
    final h = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (auth) {
      final token = await TokenStorage.getAccessToken();
      if (token != null) h['Authorization'] = 'Bearer $token';
    }
    return h;
  }

  dynamic _decode(http.Response res) {
    if (res.statusCode == 204) return null;
    final body = utf8.decode(res.bodyBytes);
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return body.isNotEmpty ? jsonDecode(body) : null;
    }
    String msg = 'Request failed';
    try {
      final err = jsonDecode(body);
      msg = err['detail'] is String
          ? err['detail']
          : err['detail']?.toString() ?? msg;
    } catch (_) {}
    throw ApiException(res.statusCode, msg);
  }

  /// Retry with refreshed access token on 401.
  Future<dynamic> _withRefresh(Future<http.Response> Function(Map<String, String>) call) async {
    var headers = await _headers();
    var res = await call(headers);
    if (res.statusCode == 401) {
      final refreshed = await _tryRefresh();
      if (refreshed) {
        headers = await _headers();
        res = await call(headers);
      }
    }
    return _decode(res);
  }

  Future<bool> _tryRefresh() async {
    try {
      final rt = await TokenStorage.getRefreshToken();
      if (rt == null) return false;
      final res = await _client.post(
        Uri.parse('${ApiConstants.baseUrl}${ApiConstants.refresh}'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': rt}),
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        await TokenStorage.saveTokens(
          accessToken: data['access_token'],
          refreshToken: data['refresh_token'],
        );
        return true;
      }
      await TokenStorage.clearAll();
      return false;
    } catch (_) {
      return false;
    }
  }

  // ── Public API ────────────────────────────────────────────────────────────

  Future<dynamic> get(String path, {bool auth = true}) => _withRefresh(
        (h) => _client.get(
          Uri.parse('${ApiConstants.baseUrl}$path'),
          headers: auth ? h : {'Accept': 'application/json'},
        ),
      );

  Future<dynamic> post(String path, Map<String, dynamic> body, {bool auth = true}) =>
      _withRefresh(
        (h) => _client.post(
          Uri.parse('${ApiConstants.baseUrl}$path'),
          headers: auth ? h : {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        ),
      );

  Future<dynamic> patch(String path, Map<String, dynamic> body) => _withRefresh(
        (h) => _client.patch(
          Uri.parse('${ApiConstants.baseUrl}$path'),
          headers: h,
          body: jsonEncode(body),
        ),
      );

  Future<dynamic> delete(String path) => _withRefresh(
        (h) => _client.delete(
          Uri.parse('${ApiConstants.baseUrl}$path'),
          headers: h,
        ),
      );
}
