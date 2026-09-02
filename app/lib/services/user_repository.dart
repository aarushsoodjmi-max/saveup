import '../models/api_models.dart';
import '../core/constants/api_constants.dart';
import 'api_client.dart';

class UserRepository {
  final _api = ApiClient();

  Future<UserProfile> getMe() async {
    final data = await _api.get(ApiConstants.me);
    return UserProfile.fromJson(data);
  }

  Future<UserProfile> updateProfile({String? name, String? email}) async {
    final body = <String, dynamic>{};
    if (name != null) body['name'] = name;
    if (email != null) body['email'] = email;
    final data = await _api.patch(ApiConstants.me, body);
    return UserProfile.fromJson(data);
  }
}
