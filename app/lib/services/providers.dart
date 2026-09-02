import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/api_models.dart';
import 'auth_repository.dart';
import 'user_repository.dart';
import 'dashboard_repository.dart';
import 'goal_repository.dart';
import 'transaction_repository.dart';
import 'payment_repository.dart';
import 'contact_withdrawal_repository.dart';
import 'token_storage.dart';

// ── Repositories ─────────────────────────────────────────────────────────

final authRepoProvider = Provider((_) => AuthRepository());
final userRepoProvider = Provider((_) => UserRepository());
final dashboardRepoProvider = Provider((_) => DashboardRepository());
final goalRepoProvider = Provider((_) => GoalRepository());
final txnRepoProvider = Provider((_) => TransactionRepository());
final paymentRepoProvider = Provider((_) => PaymentRepository());
final contactRepoProvider = Provider((_) => EmergencyContactRepository());
final withdrawalRepoProvider = Provider((_) => WithdrawalRepository());

// ── Auth state ────────────────────────────────────────────────────────────

final isLoggedInProvider = FutureProvider<bool>((ref) async {
  final token = await TokenStorage.getAccessToken();
  return token != null;
});

// ── Phone being verified (kept across login → otp screens) ───────────────

final phoneProvider = StateProvider<String>((ref) => '');
final debugOtpProvider = StateProvider<String?>((ref) => null);

// ── User profile ──────────────────────────────────────────────────────────

final userProfileProvider = FutureProvider<UserProfile>((ref) async {
  return ref.read(userRepoProvider).getMe();
});

// ── Dashboard ─────────────────────────────────────────────────────────────

final dashboardProvider = FutureProvider<DashboardData>((ref) async {
  return ref.read(dashboardRepoProvider).getDashboard();
});

// ── Goals ─────────────────────────────────────────────────────────────────

final goalsProvider = FutureProvider<List<GoalModel>>((ref) async {
  final paged = await ref.read(goalRepoProvider).listGoals(status: 'ACTIVE');
  return paged.items;
});

// ── Transactions ──────────────────────────────────────────────────────────

final transactionsProvider = FutureProvider<List<TxnModel>>((ref) async {
  final paged = await ref.read(txnRepoProvider).listTransactions(limit: 10);
  return paged.items;
});

// ── Emergency contacts ────────────────────────────────────────────────────

final emergencyContactsProvider =
    FutureProvider<List<EmergencyContact>>((ref) async {
  return ref.read(contactRepoProvider).list();
});

// ── Selected goal (for detail screen) ────────────────────────────────────

final selectedGoalProvider = StateProvider<GoalModel?>((ref) => null);
