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

// Withdrawal reason options matching backend enum
const _reasons = [
  ('MEDICAL_EMERGENCY', 'Medical Emergency'),
  ('JOB_LOSS', 'Job Loss'),
  ('NATURAL_DISASTER', 'Natural Disaster'),
  ('FAMILY_EMERGENCY', 'Family Emergency'),
  ('OTHER', 'Other'),
];

class WithdrawalScreen extends ConsumerStatefulWidget {
  final GoalModel? initialGoal;
  const WithdrawalScreen({super.key, this.initialGoal});

  @override
  ConsumerState<WithdrawalScreen> createState() => _WithdrawalState();
}

class _WithdrawalState extends ConsumerState<WithdrawalScreen> {
  _Step _step = _Step.enter;
  final _amountCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  GoalModel? _goal;
  EmergencyContact? _contact;
  String _reason = 'MEDICAL_EMERGENCY';
  bool _loading = false;
  String? _error;

  double get _amount => double.tryParse(_amountCtrl.text) ?? 0;

  @override
  void initState() {
    super.initState();
    _goal = widget.initialGoal;
  }

  @override
  void dispose() {
    _amountCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_goal == null || _contact == null) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(withdrawalRepoProvider).requestWithdrawal(
        goalId: _goal!.id,
        emergencyContactId: _contact!.id,
        amount: _amount,
        reason: _reason,
        reasonNotes: _notesCtrl.text.trim().isNotEmpty ? _notesCtrl.text.trim() : null,
      );
      ref.invalidate(goalsProvider);
      ref.invalidate(dashboardProvider);
      ref.invalidate(transactionsProvider);
      if (!mounted) return;
      setState(() => _step = _Step.success);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = 'Withdrawal request failed. Try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final goalsAsync = ref.watch(goalsProvider);
    final contactsAsync = ref.watch(emergencyContactsProvider);
    final goals = goalsAsync.valueOrNull ?? [];
    final contacts = contactsAsync.valueOrNull ?? [];

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 280),
      child: _step == _Step.success
          ? _Success(
              amount: _amount,
              goalName: _goal?.title ?? '',
              lockType: _goal?.lockType ?? 'EASY',
              onDone: () => context.go(AppRoutes.dashboard),
            )
          : _step == _Step.confirm
              ? _Confirm(
                  amount: _amount,
                  goal: _goal!,
                  contact: _contact!,
                  reason: _reason,
                  notes: _notesCtrl.text,
                  loading: _loading,
                  error: _error,
                  onBack: () => setState(() {
                    _step = _Step.enter;
                    _error = null;
                  }),
                  onConfirm: _submit,
                )
              : _Enter(
                  amountCtrl: _amountCtrl,
                  notesCtrl: _notesCtrl,
                  goals: goals,
                  contacts: contacts,
                  selectedGoal: _goal,
                  selectedContact: _contact,
                  reason: _reason,
                  amount: _amount,
                  onGoal: (g) => setState(() => _goal = g),
                  onContact: (c) => setState(() => _contact = c),
                  onReason: (r) => setState(() => _reason = r),
                  onQuick: (a) {
                    _amountCtrl.text = a;
                    setState(() {});
                  },
                  onContinue: _amount > 0 && _goal != null && _contact != null
                      ? () => setState(() => _step = _Step.confirm)
                      : null,
                ),
    );
  }
}

// ── Enter view ────────────────────────────────────────────────────────────

class _Enter extends StatelessWidget {
  final TextEditingController amountCtrl, notesCtrl;
  final List<GoalModel> goals;
  final List<EmergencyContact> contacts;
  final GoalModel? selectedGoal;
  final EmergencyContact? selectedContact;
  final String reason;
  final double amount;
  final ValueChanged<GoalModel> onGoal;
  final ValueChanged<EmergencyContact> onContact;
  final ValueChanged<String> onReason;
  final ValueChanged<String> onQuick;
  final VoidCallback? onContinue;

  const _Enter({
    required this.amountCtrl,
    required this.notesCtrl,
    required this.goals,
    required this.contacts,
    required this.selectedGoal,
    required this.selectedContact,
    required this.reason,
    required this.amount,
    required this.onGoal,
    required this.onContact,
    required this.onReason,
    required this.onQuick,
    required this.onContinue,
  });

  bool get _isHardLock => selectedGoal?.lockType == 'HARD';
  bool get _isMediumLock => selectedGoal?.lockType == 'MEDIUM';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(
              title: 'Withdraw',
              onBack: () => context.go(AppRoutes.dashboard),
            ),
            Expanded(
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Amount input
                    Center(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 24),
                        child: Column(
                          children: [
                            Text(
                              'WITHDRAWAL AMOUNT',
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.25),
                                fontSize: 10,
                                letterSpacing: 2.2,
                              ),
                            ),
                            const SizedBox(height: 16),
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.baseline,
                              textBaseline: TextBaseline.alphabetic,
                              children: [
                                Text(
                                  '₹',
                                  style: TextStyle(
                                    color: Colors.white.withOpacity(0.25),
                                    fontSize: 28,
                                  ),
                                ),
                                const SizedBox(width: 4),
                                SizedBox(
                                  width: 160,
                                  child: TextField(
                                    controller: amountCtrl,
                                    keyboardType: TextInputType.number,
                                    inputFormatters: [
                                      FilteringTextInputFormatter.digitsOnly
                                    ],
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 48,
                                      fontWeight: FontWeight.w300,
                                      height: 1,
                                    ),
                                    decoration: InputDecoration(
                                      hintText: '0',
                                      hintStyle: TextStyle(
                                        color: Colors.white.withOpacity(0.15),
                                        fontSize: 48,
                                        fontWeight: FontWeight.w300,
                                      ),
                                      border: InputBorder.none,
                                      contentPadding: EdgeInsets.zero,
                                      isDense: true,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 20),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: ['500', '1000', '2000', '5000']
                                  .map(
                                    (q) => GestureDetector(
                                      onTap: () => onQuick(q),
                                      child: Container(
                                        margin:
                                            const EdgeInsets.only(right: 8),
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 12,
                                          vertical: 6,
                                        ),
                                        decoration: BoxDecoration(
                                          color: AppColors.white05,
                                          borderRadius:
                                              BorderRadius.circular(100),
                                          border: Border.all(
                                              color: AppColors.white07),
                                        ),
                                        child: Text(
                                          '₹$q',
                                          style: const TextStyle(
                                            color: AppColors.white40,
                                            fontSize: 10.5,
                                          ),
                                        ),
                                      ),
                                    ),
                                  )
                                  .toList(),
                            ),
                          ],
                        ),
                      ),
                    ),

                    // Goal selector
                    _SectionLabel('FROM GOAL'),
                    const SizedBox(height: 12),
                    if (goals.isEmpty)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Text(
                          'No active goals.',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.30),
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ...goals.map((g) {
                      final sel = selectedGoal?.id == g.id;
                      return GestureDetector(
                        onTap: () => onGoal(g),
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color:
                                sel ? AppColors.white05 : AppColors.white03,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                              color: sel
                                  ? Colors.white.withOpacity(0.12)
                                  : AppColors.white05,
                            ),
                          ),
                          child: Row(children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    g.title,
                                    style: TextStyle(
                                      color: sel
                                          ? Colors.white.withOpacity(0.80)
                                          : Colors.white.withOpacity(0.40),
                                      fontSize: 13,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    '₹${g.savedAmount.toStringAsFixed(0)} available',
                                    style: const TextStyle(
                                      color: AppColors.white25,
                                      fontSize: 10,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            LockBadge(lockType: g.lockType),
                          ]),
                        ),
                      );
                    }),

                    // Lock warning
                    if (_isHardLock) ...[
                      const SizedBox(height: 4),
                      _Banner(
                        color: const Color(0xFFEF4444),
                        icon: Icons.lock_outline,
                        text:
                            'Hard Lock active. Emergency withdrawals require contact verification and may incur a penalty.',
                      ),
                    ] else if (_isMediumLock) ...[
                      const SizedBox(height: 4),
                      _Banner(
                        color: const Color(0xFFFBBF24),
                        icon: Icons.hourglass_top_outlined,
                        text:
                            'Medium Lock: a 48-hour cooling-off period applies before funds are released.',
                      ),
                    ],

                    const SizedBox(height: 20),

                    // Reason
                    _SectionLabel('REASON'),
                    const SizedBox(height: 12),
                    ..._reasons.map((item) {
                      final (code, label) = item;
                      final sel = reason == code;
                      return GestureDetector(
                        onTap: () => onReason(code),
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 12),
                          decoration: BoxDecoration(
                            color: sel ? AppColors.white05 : AppColors.white03,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: sel
                                  ? Colors.white.withOpacity(0.12)
                                  : AppColors.white05,
                            ),
                          ),
                          child: Row(children: [
                            Expanded(
                              child: Text(
                                label,
                                style: TextStyle(
                                  color: sel
                                      ? Colors.white.withOpacity(0.80)
                                      : Colors.white.withOpacity(0.40),
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                            Container(
                              width: 18,
                              height: 18,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: sel
                                    ? Colors.white.withOpacity(0.10)
                                    : Colors.transparent,
                                border: Border.all(
                                  color: sel
                                      ? Colors.white.withOpacity(0.50)
                                      : Colors.white.withOpacity(0.12),
                                  width: 2,
                                ),
                              ),
                            ),
                          ]),
                        ),
                      );
                    }),

                    const SizedBox(height: 20),

                    // Emergency contact
                    _SectionLabel('EMERGENCY CONTACT'),
                    const SizedBox(height: 8),
                    Text(
                      'This person will be notified of your withdrawal request.',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.20),
                        fontSize: 10.5,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (contacts.isEmpty)
                      _NoContactBanner()
                    else
                      ...contacts.map((c) {
                        final sel = selectedContact?.id == c.id;
                        return GestureDetector(
                          onTap: () => onContact(c),
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 8),
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: sel ? AppColors.white05 : AppColors.white03,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: sel
                                    ? Colors.white.withOpacity(0.12)
                                    : AppColors.white05,
                              ),
                            ),
                            child: Row(children: [
                              Container(
                                width: 36,
                                height: 36,
                                decoration: BoxDecoration(
                                  color: AppColors.white05,
                                  shape: BoxShape.circle,
                                  border: Border.all(color: AppColors.white07),
                                ),
                                child: const Icon(Icons.person_outline,
                                    size: 16, color: AppColors.white40),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      c.contactName,
                                      style: TextStyle(
                                        color: sel
                                            ? Colors.white.withOpacity(0.80)
                                            : Colors.white.withOpacity(0.40),
                                        fontSize: 13,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    Text(
                                      '${c.relationshipLabel} · ${c.phoneNumber}',
                                      style: const TextStyle(
                                        color: AppColors.white25,
                                        fontSize: 10,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Container(
                                width: 18,
                                height: 18,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: sel
                                      ? Colors.white.withOpacity(0.10)
                                      : Colors.transparent,
                                  border: Border.all(
                                    color: sel
                                        ? Colors.white.withOpacity(0.50)
                                        : Colors.white.withOpacity(0.12),
                                    width: 2,
                                  ),
                                ),
                              ),
                            ]),
                          ),
                        );
                      }),

                    const SizedBox(height: 20),

                    // Optional notes
                    _SectionLabel('NOTES (OPTIONAL)'),
                    const SizedBox(height: 12),
                    TextField(
                      controller: notesCtrl,
                      maxLines: 3,
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.70),
                        fontSize: 13,
                      ),
                      decoration: InputDecoration(
                        hintText: 'Describe the emergency...',
                        hintStyle: TextStyle(
                          color: Colors.white.withOpacity(0.15),
                        ),
                        filled: true,
                        fillColor: AppColors.white04,
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18),
                          borderSide:
                              const BorderSide(color: AppColors.white07),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18),
                          borderSide: BorderSide(
                              color: Colors.white.withOpacity(0.14)),
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16, vertical: 14),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              child: GlassButton(
                label: amount > 0
                    ? 'Request ₹${amount.toStringAsFixed(0)}'
                    : 'Enter an Amount',
                enabled: amount > 0 &&
                    selectedGoal != null &&
                    selectedContact != null,
                variant: amount > 0
                    ? GlassButtonVariant.danger
                    : GlassButtonVariant.subtle,
                onTap: onContinue,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Confirm view ──────────────────────────────────────────────────────────

class _Confirm extends StatelessWidget {
  final double amount;
  final GoalModel goal;
  final EmergencyContact contact;
  final String reason;
  final String notes;
  final bool loading;
  final String? error;
  final VoidCallback onBack, onConfirm;

  const _Confirm({
    required this.amount,
    required this.goal,
    required this.contact,
    required this.reason,
    required this.notes,
    required this.loading,
    required this.error,
    required this.onBack,
    required this.onConfirm,
  });

  String get _reasonLabel =>
      _reasons.firstWhere((r) => r.$1 == reason, orElse: () => (reason, reason)).$2;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(title: 'Confirm Withdrawal', onBack: onBack),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                child: Column(children: [
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('WITHDRAWING',
                            style: TextStyle(
                                color: Colors.white.withOpacity(0.28),
                                fontSize: 10,
                                letterSpacing: 1.8)),
                        const SizedBox(height: 6),
                        Text(
                          '₹${amount.toStringAsFixed(0)}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 32,
                            fontWeight: FontWeight.w600,
                            height: 1,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('FROM GOAL',
                            style: TextStyle(
                                color: Colors.white.withOpacity(0.28),
                                fontSize: 10,
                                letterSpacing: 1.8)),
                        const SizedBox(height: 6),
                        Text(goal.title,
                            style: const TextStyle(
                                color: AppColors.white80,
                                fontSize: 14,
                                fontWeight: FontWeight.w500)),
                        Text(
                          '₹${goal.savedAmount.toStringAsFixed(0)} available',
                          style: const TextStyle(
                              color: AppColors.white30, fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('REASON',
                            style: TextStyle(
                                color: Colors.white.withOpacity(0.28),
                                fontSize: 10,
                                letterSpacing: 1.8)),
                        const SizedBox(height: 6),
                        Text(_reasonLabel,
                            style: const TextStyle(
                                color: AppColors.white80,
                                fontSize: 13,
                                fontWeight: FontWeight.w500)),
                        if (notes.trim().isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(notes,
                              style: const TextStyle(
                                  color: AppColors.white40, fontSize: 12)),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('EMERGENCY CONTACT',
                            style: TextStyle(
                                color: Colors.white.withOpacity(0.28),
                                fontSize: 10,
                                letterSpacing: 1.8)),
                        const SizedBox(height: 6),
                        Text(contact.contactName,
                            style: const TextStyle(
                                color: AppColors.white80,
                                fontSize: 13,
                                fontWeight: FontWeight.w500)),
                        Text(
                          '${contact.relationshipLabel} · ${contact.phoneNumber}',
                          style: const TextStyle(
                              color: AppColors.white30, fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0x0FFBBF24),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: const Color(0x26FBBF24)),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.shield_outlined,
                            size: 13, color: Color(0x99FBBF24)),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'Your emergency contact will be notified. Withdrawal processed in 1–2 business days.',
                            style: TextStyle(
                              color: const Color(0xFFCA8A04).withOpacity(0.55),
                              fontSize: 11,
                              height: 1.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (error != null) ...[
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0x0FEF4444),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0x24EF4444)),
                      ),
                      child: Text(error!,
                          style: const TextStyle(
                              color: Color(0xCCEF4444), fontSize: 12)),
                    ),
                  ],
                ]),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              child: Column(children: [
                GlassButton(
                  label: 'Confirm Withdrawal',
                  variant: GlassButtonVariant.danger,
                  loading: loading,
                  onTap: onConfirm,
                ),
                const SizedBox(height: 8),
                GestureDetector(
                  onTap: onBack,
                  child: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 8),
                    child: Text('Cancel',
                        style: TextStyle(
                            color: AppColors.white25, fontSize: 12.5)),
                  ),
                ),
              ]),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Success view ──────────────────────────────────────────────────────────

class _Success extends StatelessWidget {
  final double amount;
  final String goalName, lockType;
  final VoidCallback onDone;

  const _Success({
    required this.amount,
    required this.goalName,
    required this.lockType,
    required this.onDone,
  });

  @override
  Widget build(BuildContext context) {
    final isMedium = lockType == 'MEDIUM';
    final isHard = lockType == 'HARD';
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 68,
                height: 68,
                decoration: BoxDecoration(
                  color: AppColors.white04,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.white07),
                ),
                child: const Icon(Icons.arrow_upward,
                    size: 26, color: AppColors.white50),
              ),
              const SizedBox(height: 20),
              const Text(
                'Request Sent.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 34,
                  fontFamily: 'Georgia',
                  fontWeight: FontWeight.w400,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                isHard
                    ? 'Your request is under review. Your emergency contact has been notified.'
                    : isMedium
                        ? 'A 48-hour cooling period applies. Funds will be released automatically.'
                        : '₹${amount.toStringAsFixed(0)} will be credited in 1–2 business days.',
                textAlign: TextAlign.center,
                style: TextStyle(
                    color: Colors.white.withOpacity(0.30),
                    fontSize: 13,
                    height: 1.5),
              ),
              const SizedBox(height: 40),
              GlassButton(
                label: 'Back to Dashboard',
                variant: GlassButtonVariant.subtle,
                onTap: onDone,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: TextStyle(
        color: Colors.white.withOpacity(0.25),
        fontSize: 10,
        letterSpacing: 2.2,
        fontWeight: FontWeight.w500,
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  final Color color;
  final IconData icon;
  final String text;
  const _Banner({required this.color, required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withOpacity(0.06),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.22)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 13, color: color.withOpacity(0.60)),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                color: color.withOpacity(0.55),
                fontSize: 11,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NoContactBanner extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.white03,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.white07),
      ),
      child: Row(
        children: [
          const Icon(Icons.person_add_outlined,
              size: 14, color: AppColors.white25),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'No emergency contacts added. Go to Profile → Security to add one.',
              style: TextStyle(
                color: Colors.white.withOpacity(0.30),
                fontSize: 11,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
