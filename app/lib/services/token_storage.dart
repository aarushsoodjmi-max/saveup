import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../core/constants/app_constants.dart';

class TokenStorage {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(
        key: AppConstants.storageKeyAccessToken, value: accessToken);
    await _storage.write(
        key: AppConstants.storageKeyRefreshToken, value: refreshToken);
  }

  static Future<String?> getAccessToken() =>
      _storage.read(key: AppConstants.storageKeyAccessToken);

  static Future<String?> getRefreshToken() =>
      _storage.read(key: AppConstants.storageKeyRefreshToken);

  static Future<void> clearAll() => _storage.deleteAll();
}
