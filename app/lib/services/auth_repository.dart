import '../models/api_models.dart';
import '../core/constants/api_constants.dart';
import 'api_client.dart';
import 'token_storage.dart';

class AuthRepository {
  final _api = ApiClient();

  Future<SendOtpResponse> sendOtp(String phoneNumber) async {
    final data = await _api.post(
      ApiConstants.sendOtp,
      {'phone_number': phoneNumber},
      auth: false,
    );
    return SendOtpResponse.fromJson(data);
  }

  Future<AuthResponse> verifyOtp(
    String phoneNumber,
    String otp, {
    String? name,
  }) async {
    final body = <String, dynamic>{
      'phone_number': phoneNumber,
      'otp': otp,
    };
    if (name != null && name.isNotEmpty) body['name'] = name;

    final data = await _api.post(ApiConstants.verifyOtp, body, auth: false);
    final auth = AuthResponse.fromJson(data);
    await TokenStorage.saveTokens(
      accessToken: auth.accessToken,
      refreshToken: auth.refreshToken,
    );
    return auth;
  }

  Future<void> logout() async {
    final rt = await TokenStorage.getRefreshToken();
    if (rt != null) {
      try {
        await _api.post(ApiConstants.logout, {'refresh_token': rt});
      } catch (_) {}
    }
    await TokenStorage.clearAll();
  }
}
