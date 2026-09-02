import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/goal.dart';
import '../models/transaction.dart';

final goalsProvider = StateProvider<List<Goal>>((ref) => sampleGoals);

final txnsProvider = StateProvider<List<Txn>>((ref) => sampleTxns);

final selectedGoalProvider = StateProvider<Goal>((ref) => sampleGoals[0]);

final totalSavedProvider = Provider<int>((ref) {
  final goals = ref.watch(goalsProvider);
  return goals.fold(0, (sum, g) => sum + g.saved);
});
