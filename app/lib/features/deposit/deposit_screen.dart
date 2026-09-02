import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../models/api_models.dart';
import '../../routes/app_router.dart';
import '../../services/providers.dart';
import '../../services/api_client.dart';
import '../../widgets/glass_button.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/shared_widgets.dart';

enum _Step { enter, confirm, success }

class DepositScreen extends ConsumerStatefulWidget {
  final GoalModel? initialGoal;
  const DepositScreen({super.key, this.initialGoal});

  @override
  ConsumerState<DepositScreen> createState() => _DepositState();
}

class _DepositState extends ConsumerState<DepositScreen> {
  _Step _step = _Step.enter;
  final _amountCtrl = TextEditingController();
  GoalModel? _goal;
  bool _loading = false;
  String? _error;
  int _bankIdx = 0;

  final _banks = [
    ('HDFC Bank', '•••• 1234', 'Savings'),
    ('ICICI Bank', '•••• 5678', 'Current'),
  ];

  double get _amount => double.tryParse(_amountCtrl.text) ?? 0;

  @override
  void initState() {
    super.initState();
    _goal = widget.initialGoal;
  }

  @override
  void dispose() {
    _amountCtrl.dispose();
    super.dispose();
  }

  Future<void> _confirm() async {
    if (_goal == null) return;
    setState(() { _loading = true; _error = null; });
    try {
      // 1. Create payment order
      final order = await ref.read(paymentRepoProvider).createOrder(_goal!.id, _amount);
      // 2. Verify (mock – passes provider_order_id as signature)
      await ref.read(paymentRepoProvider).verifyPayment(
        paymentOrderId: order.id,
        providerOrderId: order.providerOrderId,
        providerPaymentId: 'pay_${DateTime.now().millisecondsSinceEpoch}',
      );
      ref.invalidate(goalsProvider);
      ref.invalidate(dashboardProvider);
      ref.invalidate(transactionsProvider);
      if (!mounted) return;
      setState(() => _step = _Step.success);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = 'Payment failed. Please try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final goalsAsync = ref.watch(goalsProvider);
    final goals = goalsAsync.valueOrNull ?? [];

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 280),
      child: _step == _Step.success
          ? _Success(amount: _amount, goalName: _goal?.title ?? '', onDone: () => context.go(AppRoutes.dashboard))
          : _step == _Step.confirm
              ? _Confirm(
                  amount: _amount, goal: _goal!, bank: _banks[_bankIdx],
                  loading: _loading, error: _error,
                  onBack: () => setState(() { _step = _Step.enter; _error = null; }),
                  onConfirm: _confirm,
                )
              : _Enter(
                  amountCtrl: _amountCtrl, goals: goals, selectedGoal: _goal,
                  bankIdx: _bankIdx, banks: _banks, amount: _amount,
                  onGoal: (g) => setState(() => _goal = g),
                  onBank: (i) => setState(() => _bankIdx = i),
                  onQuick: (a) { _amountCtrl.text = a; setState(() {}); },
                  onContinue: _amount > 0 && _goal != null
                      ? () => setState(() => _step = _Step.confirm)
                      : null,
                ),
    );
  }
}

// ── Enter ─────────────────────────────────────────────────────────────────

class _Enter extends StatelessWidget {
  final TextEditingController amountCtrl;
  final List<GoalModel> goals;
  final GoalModel? selectedGoal;
  final int bankIdx;
  final List<(String, String, String)> banks;
  final double amount;
  final ValueChanged<GoalModel> onGoal;
  final ValueChanged<int> onBank;
  final ValueChanged<String> onQuick;
  final VoidCallback? onContinue;

  const _Enter({
    required this.amountCtrl, required this.goals, required this.selectedGoal,
    required this.bankIdx, required this.banks, required this.amount,
    required this.onGoal, required this.onBank, required this.onQuick,
    required this.onContinue,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(title: 'Add Money', onBack: () => context.go(AppRoutes.dashboard)),
            Expanded(
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 28),
                        child: Column(
                          children: [
                            Text('ENTER AMOUNT', style: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 10, letterSpacing: 2.2)),
                            const SizedBox(height: 16),
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.baseline, textBaseline: TextBaseline.alphabetic,
                              children: [
                                Text('₹', style: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 28)),
                                const SizedBox(width: 4),
                                SizedBox(
                                  width: 160,
                                  child: TextField(
                                    controller: amountCtrl,
                                    keyboardType: TextInputType.number,
                                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(color: Colors.white, fontSize: 48, fontWeight: FontWeight.w300, height: 1),
                                    decoration: InputDecoration(
                                      hintText: '0',
                                      hintStyle: TextStyle(color: Colors.white.withOpacity(0.15), fontSize: 48, fontWeight: FontWeight.w300),
                                      border: InputBorder.none, contentPadding: EdgeInsets.zero, isDense: true,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 20),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: ['500', '1000', '2500', '5000'].map((q) =>
                                GestureDetector(
                                  onTap: () => onQuick(q),
                                  child: Container(
                                    margin: const EdgeInsets.only(right: 8),
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                    decoration: BoxDecoration(color: AppColors.white05, borderRadius: BorderRadius.circular(100), border: Border.all(color: AppColors.white07)),
                                    child: Text('+₹$q', style: const TextStyle(color: AppColors.white40, fontSize: 10.5)),
                                  ),
                                ),
                              ).toList(),
                            ),
                          ],
                        ),
                      ),
                    ),
                    _Label('SELECT GOAL'),
                    const SizedBox(height: 12),
                    if (goals.isEmpty)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Text('No goals yet. Create one first.',
                          style: TextStyle(color: Colors.white.withOpacity(0.30), fontSize: 12)),
                      ),
                    ...goals.map((g) {
                      final sel = selectedGoal?.id == g.id;
                      return GestureDetector(
                        onTap: () => onGoal(g),
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: sel ? const Color(0x0F10B981) : AppColors.white03,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: sel ? const Color(0x3810B981) : AppColors.white07),
                          ),
                          child: Row(children: [
                            ClipRRect(borderRadius: BorderRadius.circular(8),
                              child: SizedBox(width: 40, height: 40,
                                child: Image.network(g.imageUrlOrFallback, fit: BoxFit.cover,
                                  opacity: const AlwaysStoppedAnimation(0.65),
                                  errorBuilder: (_, __, ___) => Container(color: AppColors.white05)),
                              )),
                            const SizedBox(width: 12),
                            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(g.title, maxLines: 1, overflow: TextOverflow.ellipsis,
                                style: TextStyle(color: sel ? Colors.white.withOpacity(0.85) : Colors.white.withOpacity(0.45), fontSize: 13, fontWeight: FontWeight.w500)),
                              Text('${g.progressPercentage.toStringAsFixed(0)}% · ₹${g.savedAmount.toStringAsFixed(0)}',
                                style: const TextStyle(color: AppColors.white25, fontSize: 10)),
                            ])),
                            Container(width: 18, height: 18,
                              decoration: BoxDecoration(shape: BoxShape.circle,
                                color: sel ? const Color(0x2610B981) : Colors.transparent,
                                border: Border.all(color: sel ? AppColors.emerald : Colors.white.withOpacity(0.12), width: 2)),
                              child: sel ? Container(margin: const EdgeInsets.all(3), decoration: const BoxDecoration(color: AppColors.emerald, shape: BoxShape.circle)) : null),
                          ]),
                        ),
                      );
                    }),
                    const SizedBox(height: 20),
                    _Label('FROM BANK'),
                    const SizedBox(height: 12),
                    ...List.generate(banks.length, (i) {
                      final (name, acc, type) = banks[i];
                      final sel = bankIdx == i;
                      return GestureDetector(
                        onTap: () => onBank(i),
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: sel ? AppColors.white05 : AppColors.white03,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: sel ? Colors.white.withOpacity(0.12) : AppColors.white05),
                          ),
                          child: Row(children: [
                            Container(width: 36, height: 36,
                              decoration: BoxDecoration(color: AppColors.white05, borderRadius: BorderRadius.circular(10), border: Border.all(color: AppColors.white07)),
                              child: const Icon(Icons.credit_card_outlined, size: 14, color: AppColors.white40)),
                            const SizedBox(width: 12),
                            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(name, style: TextStyle(color: sel ? Colors.white.withOpacity(0.80) : Colors.white.withOpacity(0.40), fontSize: 13, fontWeight: FontWeight.w500)),
                              Text('$acc · $type', style: const TextStyle(color: AppColors.white25, fontSize: 10)),
                            ])),
                            Container(width: 18, height: 18,
                              decoration: BoxDecoration(shape: BoxShape.circle,
                                color: sel ? Colors.white.withOpacity(0.10) : Colors.transparent,
                                border: Border.all(color: sel ? Colors.white.withOpacity(0.50) : Colors.white.withOpacity(0.12), width: 2))),
                          ]),
                        ),
                      );
                    }),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              child: GlassButton(
                label: amount > 0 ? 'Add ₹${amount.toStringAsFixed(0)}' : 'Enter an Amount',
                enabled: amount > 0 && selectedGoal != null,
                onTap: onContinue,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Confirm ───────────────────────────────────────────────────────────────

class _Confirm extends StatelessWidget {
  final double amount;
  final GoalModel goal;
  final (String, String, String) bank;
  final bool loading;
  final String? error;
  final VoidCallback onBack, onConfirm;
  const _Confirm({required this.amount, required this.goal, required this.bank,
    required this.loading, required this.error, required this.onBack, required this.onConfirm});

  @override
  Widget build(BuildContext context) {
    final (bankName, acc, type) = bank;
    final afterPct = ((goal.savedAmount + amount) / goal.targetAmount * 100).clamp(0.0, 100.0);
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(title: 'Confirm Deposit', onBack: onBack),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                child: Column(children: [
                  GlassCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('AMOUNT', style: TextStyle(color: Colors.white.withOpacity(0.28), fontSize: 10, letterSpacing: 1.8)),
                    const SizedBox(height: 6),
                    Text('₹${amount.toStringAsFixed(0)}', style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.w600, height: 1)),
                  ])),
                  const SizedBox(height: 10),
                  GlassCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('TO GOAL', style: TextStyle(color: Colors.white.withOpacity(0.28), fontSize: 10, letterSpacing: 1.8)),
                    const SizedBox(height: 8),
                    Text(goal.title, style: const TextStyle(color: AppColors.white80, fontSize: 14, fontWeight: FontWeight.w500)),
                    const SizedBox(height: 12),
                    AppProgressBar(value: goal.progressPercentage),
                    const SizedBox(height: 6),
                    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                      Text('${goal.progressPercentage.toStringAsFixed(0)}%', style: const TextStyle(color: AppColors.white25, fontSize: 10)),
                      Text('${afterPct.toStringAsFixed(0)}% after deposit', style: const TextStyle(color: Color(0x9934D399), fontSize: 10)),
                    ]),
                  ])),
                  const SizedBox(height: 10),
                  GlassCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('FROM BANK', style: TextStyle(color: Colors.white.withOpacity(0.28), fontSize: 10, letterSpacing: 1.8)),
                    const SizedBox(height: 8),
                    Text(bankName, style: const TextStyle(color: AppColors.white80, fontSize: 14, fontWeight: FontWeight.w500)),
                    Text('$acc · $type', style: const TextStyle(color: AppColors.white30, fontSize: 11)),
                  ])),
                  if (error != null) ...[
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(color: const Color(0x0FEF4444), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0x24EF4444))),
                      child: Text(error!, style: const TextStyle(color: Color(0xCCEF4444), fontSize: 12)),
                    ),
                  ],
                ]),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              child: Column(children: [
                GlassButton(label: 'Confirm Deposit', loading: loading, onTap: onConfirm),
                const SizedBox(height: 8),
                GestureDetector(onTap: onBack,
                  child: const Padding(padding: EdgeInsets.symmetric(vertical: 8),
                    child: Text('Edit Amount', style: TextStyle(color: AppColors.white25, fontSize: 12.5)))),
              ]),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Success ───────────────────────────────────────────────────────────────

class _Success extends StatelessWidget {
  final double amount;
  final String goalName;
  final VoidCallback onDone;
  const _Success({required this.amount, required this.goalName, required this.onDone});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            Container(width: 68, height: 68,
              decoration: BoxDecoration(color: const Color(0x1410B981), shape: BoxShape.circle, border: Border.all(color: const Color(0x3310B981))),
              child: const Icon(Icons.check, size: 28, color: AppColors.emeraldLight)),
            const SizedBox(height: 20),
            const Text('Money Added.', textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white, fontSize: 34, fontFamily: 'Georgia', fontWeight: FontWeight.w400)),
            const SizedBox(height: 8),
            Text('₹${amount.toStringAsFixed(0)} added to', textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white.withOpacity(0.30), fontSize: 13)),
            const SizedBox(height: 4),
            Text(goalName, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.white60, fontSize: 13, fontWeight: FontWeight.w500)),
            const SizedBox(height: 40),
            GlassButton(label: 'Back to Dashboard', onTap: onDone),
          ]),
        ),
      ),
    );
  }
}

class _Label extends StatelessWidget {
  final String text;
  const _Label(this.text);
  @override
  Widget build(BuildContext context) => Text(text,
    style: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 10, letterSpacing: 2.2, fontWeight: FontWeight.w500));
}
