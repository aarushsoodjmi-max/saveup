import '../models/api_models.dart';
import '../core/constants/api_constants.dart';
import 'api_client.dart';

class GoalRepository {
  final _api = ApiClient();

  Future<Paginated<GoalModel>> listGoals({
    String? status,
    int page = 1,
    int limit = 50,
  }) async {
    var path = '${ApiConstants.goals}?page=$page&limit=$limit';
    if (status != null) path += '&status=$status';
    final data = await _api.get(path);
    return Paginated.fromJson(data, GoalModel.fromJson);
  }

  Future<GoalModel> getGoal(String id) async {
    final data = await _api.get(ApiConstants.goal(id));
    return GoalModel.fromJson(data);
  }

  Future<GoalModel> createGoal({
    required String title,
    required String category,
    required double targetAmount,
    required String lockType,
    String? description,
    String? deadline,
    double? monthlyTarget,
  }) async {
    final body = <String, dynamic>{
      'title': title,
      'category': category,
      'target_amount': targetAmount,
      'lock_type': lockType,
    };
    if (description != null) body['description'] = description;
    if (deadline != null) body['deadline'] = deadline;
    if (monthlyTarget != null) body['monthly_target'] = monthlyTarget;
    final data = await _api.post(ApiConstants.goals, body);
    return GoalModel.fromJson(data);
  }

  Future<GoalModel> updateGoal(
    String id, {
    String? title,
    String? category,
    double? targetAmount,
    String? description,
    String? deadline,
  }) async {
    final body = <String, dynamic>{};
    if (title != null) body['title'] = title;
    if (category != null) body['category'] = category;
    if (targetAmount != null) body['target_amount'] = targetAmount;
    if (description != null) body['description'] = description;
    if (deadline != null) body['deadline'] = deadline;
    final data = await _api.patch(ApiConstants.goal(id), body);
    return GoalModel.fromJson(data);
  }

  Future<TxnModel> withdrawFromEasyGoal(String id, double amount) async {
    final data = await _api.post(
      ApiConstants.goalWithdraw(id),
      {'amount': amount},
    );
    return TxnModel.fromJson(data);
  }
}
