import '../models/api_models.dart';
import '../core/constants/api_constants.dart';
import 'api_client.dart';

class PaymentRepository {
  final _api = ApiClient();

  Future<PaymentOrder> createOrder(String goalId, double amount) async {
    final data = await _api.post(ApiConstants.createOrder, {
      'goal_id': goalId,
      'amount': amount,
    });
    return PaymentOrder.fromJson(data);
  }

  /// Verifies a payment with the mock provider.
  /// For the mock, signature = provider_order_id (from the backend's mock
  /// payment_provider.py which accepts any signature).
  Future<Map<String, dynamic>> verifyPayment({
    required String paymentOrderId,
    required String providerOrderId,
    required String providerPaymentId,
  }) async {
    final data = await _api.post(ApiConstants.verifyPayment, {
      'payment_order_id': paymentOrderId,
      'provider_payment_id': providerPaymentId,
      'signature': providerOrderId, // mock accepts anything
    });
    return Map<String, dynamic>.from(data);
  }
}
