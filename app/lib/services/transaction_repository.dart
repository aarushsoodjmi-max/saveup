import '../models/api_models.dart';
import '../core/constants/api_constants.dart';
import 'api_client.dart';

class TransactionRepository {
  final _api = ApiClient();

  Future<Paginated<TxnModel>> listTransactions({
    String? goalId,
    String? transactionType,
    int page = 1,
    int limit = 20,
  }) async {
    var path = '${ApiConstants.transactions}?page=$page&limit=$limit';
    if (goalId != null) path += '&goal_id=$goalId';
    if (transactionType != null) path += '&transaction_type=$transactionType';
    final data = await _api.get(path);
    return Paginated.fromJson(data, TxnModel.fromJson);
  }
}
