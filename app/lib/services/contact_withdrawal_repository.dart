import '../models/api_models.dart';
import '../core/constants/api_constants.dart';
import 'api_client.dart';

class EmergencyContactRepository {
  final _api = ApiClient();

  Future<List<EmergencyContact>> list() async {
    final data = await _api.get(ApiConstants.emergencyContacts);
    return (data as List).map((e) => EmergencyContact.fromJson(e)).toList();
  }

  Future<EmergencyContact> create({
    required String contactName,
    required String relationshipLabel,
    required String phoneNumber,
  }) async {
    final data = await _api.post(ApiConstants.emergencyContacts, {
      'contact_name': contactName,
      'relationship_label': relationshipLabel,
      'phone_number': phoneNumber,
    });
    return EmergencyContact.fromJson(data);
  }

  Future<void> delete(String id) =>
      _api.delete(ApiConstants.emergencyContact(id));
}

class WithdrawalRepository {
  final _api = ApiClient();

  Future<WithdrawalModel> requestWithdrawal({
    required String goalId,
    required String emergencyContactId,
    required double amount,
    required String reason,
    String? reasonNotes,
  }) async {
    final body = <String, dynamic>{
      'goal_id': goalId,
      'emergency_contact_id': emergencyContactId,
      'amount': amount,
      'reason': reason,
    };
    if (reasonNotes != null) body['reason_notes'] = reasonNotes;
    final data = await _api.post(ApiConstants.withdrawals, body);
    return WithdrawalModel.fromJson(data);
  }

  Future<Paginated<WithdrawalModel>> list({int page = 1, int limit = 20}) async {
    final data =
        await _api.get('${ApiConstants.withdrawals}?page=$page&limit=$limit');
    return Paginated.fromJson(data, WithdrawalModel.fromJson);
  }

  Future<WithdrawalModel> get(String id) async {
    final data = await _api.get(ApiConstants.withdrawal(id));
    return WithdrawalModel.fromJson(data);
  }

  Future<WithdrawalModel> cancel(String id) async {
    final data = await _api.post(ApiConstants.withdrawalCancel(id), {});
    return WithdrawalModel.fromJson(data);
  }

  Future<WithdrawalModel> complete(String id) async {
    final data = await _api.post(ApiConstants.withdrawalComplete(id), {});
    return WithdrawalModel.fromJson(data);
  }
}
