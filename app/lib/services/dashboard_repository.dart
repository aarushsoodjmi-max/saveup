import '../models/api_models.dart';
import '../core/constants/api_constants.dart';
import 'api_client.dart';

class DashboardRepository {
  final _api = ApiClient();

  Future<DashboardData> getDashboard() async {
    final data = await _api.get(ApiConstants.dashboard);
    return DashboardData.fromJson(data);
  }
}
