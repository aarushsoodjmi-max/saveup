import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../routes/app_router.dart';
import '../../services/providers.dart';
import '../../services/api_client.dart';
import '../../widgets/glass_button.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/shared_widgets.dart';

class CreateGoalScreen extends ConsumerStatefulWidget {
  const CreateGoalScreen({super.key});

  @override
  ConsumerState<CreateGoalScreen> createState() => _CreateGoalState();
}

class _CreateGoalState extends ConsumerState<CreateGoalScreen> {
  int _step = 1;
  final _nameCtrl = TextEditingController();
  final _amountCtrl = TextEditingController();
  String _category = '';
  String _lock = 'EASY';
  String _duration = '';
  bool _loading = false;
  String? _error;

  static const _categories = [
    'Gadgets', 'Travel', 'Vehicle', 'Home', 'Education', 'Emergency'
  ];
  static const _locks = [
    ('EASY', 'Easy Lock', 'Withdraw anytime. No restrictions.'),
    ('MEDIUM', 'Medium Lock', '48-hour cooling period before withdrawal.'),
    ('HARD', 'Hard Lock', 'Cannot withdraw until target is fully met.'),
  ];

  @override
  void dispose() {
    _nameCtrl.dispose();
    _amountCtrl.dispose();
    super.dispose();
  }

  void _back() {
    if (_step > 1) setState(() => _step--);
    else context.go(AppRoutes.dashboard);
  }

  Future<void> _next() async {
    if (_step < 3) {
      setState(() => _step++);
      return;
    }
    setState(() { _loading = true; _error = null; });
    try {
      final amount = double.tryParse(_amountCtrl.text) ?? 0;
      await ref.read(goalRepoProvider).createGoal(
        title: _nameCtrl.text.trim(),
        category: _category,
        targetAmount: amount,
        lockType: _lock,
      );
      ref.invalidate(goalsProvider);
      ref.invalidate(dashboardProvider);
      if (!mounted) return;
      context.go(AppRoutes.dashboard);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = 'Something went wrong. Try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      resizeToAvoidBottomInset: true,
      body: SafeArea(
        child: Column(
          children: [
            _header(),
            Expanded(
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 0),
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 220),
                  child: KeyedSubtree(
                    key: ValueKey(_step),
                    child: _step == 1 ? _Step1(
                      nameCtrl: _nameCtrl,
                      category: _category,
                      categories: _categories,
                      onCategory: (c) => setState(() => _category = c),
                    ) : _step == 2 ? _Step2(
                      amountCtrl: _amountCtrl,
                      duration: _duration,
                      onDuration: (d) => setState(() => _duration = d),
                      onQuick: (a) { _amountCtrl.text = a; setState(() {}); },
                    ) : _Step3(
                      lock: _lock,
                      locks: _locks,
                      name: _nameCtrl.text,
                      amount: _amountCtrl.text,
                      onLock: (l) => setState(() => _lock = l),
                    ),
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              child: Column(
                children: [
                  if (_error != null) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      margin: const EdgeInsets.only(bottom: 10),
                      decoration: BoxDecoration(
                        color: const Color(0x0FEF4444),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0x24EF4444)),
                      ),
                      child: Text(_error!,
                          style: const TextStyle(
                              color: Color(0xCCEF4444), fontSize: 12)),
                    ),
                  ],
                  GlassButton(
                    label: _step < 3 ? 'Continue' : 'Create Goal',
                    loading: _loading,
                    onTap: _next,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _header() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
      child: Column(
        children: [
          Row(
            children: [
              GestureDetector(
                onTap: _back,
                child: Container(
                  width: 36, height: 36,
                  decoration: BoxDecoration(
                    color: AppColors.white05, shape: BoxShape.circle,
                    border: Border.all(color: AppColors.white07),
                  ),
                  child: const Icon(Icons.chevron_left, color: AppColors.white50, size: 20),
                ),
              ),
              const SizedBox(width: 12),
              const Text('New Goal',
                  style: TextStyle(color: AppColors.white80, fontSize: 13.5, fontWeight: FontWeight.w500)),
              const Spacer(),
              Text('$_step / 3',
                  style: const TextStyle(color: AppColors.white20, fontSize: 11)),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: List.generate(3, (i) => Expanded(
              child: Container(
                margin: EdgeInsets.only(right: i < 2 ? 8 : 0),
                height: 2,
                decoration: BoxDecoration(
                  color: i + 1 <= _step ? AppColors.emerald : AppColors.white07,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            )),
          ),
        ],
      ),
    );
  }
}

class _Step1 extends StatelessWidget {
  final TextEditingController nameCtrl;
  final String category;
  final List<String> categories;
  final ValueChanged<String> onCategory;
  const _Step1({required this.nameCtrl, required this.category, required this.categories, required this.onCategory});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),
        const Text('Name your goal.',
            style: TextStyle(color: Colors.white, fontSize: 32, fontFamily: 'Georgia', fontWeight: FontWeight.w400, height: 1.1)),
        const SizedBox(height: 4),
        Text('What are you saving for?', style: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 12.5)),
        const SizedBox(height: 28),
        TextField(
          controller: nameCtrl,
          style: const TextStyle(color: Colors.white, fontSize: 15),
          decoration: InputDecoration(
            hintText: 'e.g., Dream Vacation, New MacBook...',
            hintStyle: TextStyle(color: Colors.white.withOpacity(0.15)),
            filled: true, fillColor: AppColors.white04,
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color: AppColors.white07)),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color: Color(0x4010B981))),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          ),
        ),
        const SizedBox(height: 32),
        Text('CATEGORY', style: TextStyle(color: Colors.white.withOpacity(0.28), fontSize: 10, letterSpacing: 2.2, fontWeight: FontWeight.w500)),
        const SizedBox(height: 12),
        GridView.count(
          crossAxisCount: 3, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 8, crossAxisSpacing: 8, childAspectRatio: 2.8,
          children: categories.map((cat) {
            final sel = category == cat;
            return GestureDetector(
              onTap: () => onCategory(cat),
              child: Container(
                decoration: BoxDecoration(
                  color: sel ? const Color(0x1410B981) : AppColors.white03,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: sel ? const Color(0x4010B981) : AppColors.white07),
                ),
                child: Center(child: Text(cat, style: TextStyle(color: sel ? const Color(0xE634D399) : Colors.white.withOpacity(0.40), fontSize: 11.5, fontWeight: FontWeight.w500))),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 24),
      ],
    );
  }
}

class _Step2 extends StatelessWidget {
  final TextEditingController amountCtrl;
  final String duration;
  final ValueChanged<String> onDuration;
  final ValueChanged<String> onQuick;
  const _Step2({required this.amountCtrl, required this.duration, required this.onDuration, required this.onQuick});

  @override
  Widget build(BuildContext context) {
    final durs = ['3 mo', '6 mo', '1 yr', '2 yr'];
    final quicks = ['10000', '50000', '100000', '500000'];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),
        const Text('Set your target.', style: TextStyle(color: Colors.white, fontSize: 32, fontFamily: 'Georgia', fontWeight: FontWeight.w400, height: 1.1)),
        const SizedBox(height: 28),
        Container(
          decoration: BoxDecoration(color: AppColors.white04, borderRadius: BorderRadius.circular(18), border: Border.all(color: AppColors.white07)),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.baseline, textBaseline: TextBaseline.alphabetic,
            children: [
              Text('₹', style: TextStyle(color: Colors.white.withOpacity(0.30), fontSize: 28)),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: amountCtrl,
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  style: const TextStyle(color: Colors.white, fontSize: 36, fontWeight: FontWeight.w300, height: 1),
                  decoration: InputDecoration(
                    hintText: '0',
                    hintStyle: TextStyle(color: Colors.white.withOpacity(0.15), fontSize: 36, fontWeight: FontWeight.w300),
                    border: InputBorder.none, contentPadding: EdgeInsets.zero, isDense: true,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: quicks.map((q) {
            final val = int.parse(q);
            final label = val >= 100000 ? '₹${val ~/ 100000}L' : '₹${val ~/ 1000}K';
            return Expanded(
              child: GestureDetector(
                onTap: () => onQuick(q),
                child: Container(
                  margin: EdgeInsets.only(right: q != quicks.last ? 8 : 0),
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(color: AppColors.white04, borderRadius: BorderRadius.circular(12), border: Border.all(color: AppColors.white07)),
                  child: Center(child: Text(label, style: const TextStyle(color: AppColors.white40, fontSize: 9.5, fontWeight: FontWeight.w500))),
                ),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 32),
        Text('DURATION', style: TextStyle(color: Colors.white.withOpacity(0.28), fontSize: 10, letterSpacing: 2.2, fontWeight: FontWeight.w500)),
        const SizedBox(height: 12),
        Row(
          children: durs.map((d) {
            final sel = duration == d;
            return Expanded(
              child: GestureDetector(
                onTap: () => onDuration(d),
                child: Container(
                  margin: EdgeInsets.only(right: d != durs.last ? 8 : 0),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(
                    color: sel ? const Color(0x1410B981) : AppColors.white03,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: sel ? const Color(0x4010B981) : AppColors.white07),
                  ),
                  child: Center(child: Text(d, style: TextStyle(color: sel ? const Color(0xE634D399) : Colors.white.withOpacity(0.40), fontSize: 11, fontWeight: FontWeight.w500))),
                ),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 24),
      ],
    );
  }
}

class _Step3 extends StatelessWidget {
  final String lock;
  final List<(String, String, String)> locks;
  final String name, amount;
  final ValueChanged<String> onLock;
  const _Step3({required this.lock, required this.locks, required this.name, required this.amount, required this.onLock});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),
        const Text('Choose a lock.', style: TextStyle(color: Colors.white, fontSize: 32, fontFamily: 'Georgia', fontWeight: FontWeight.w400, height: 1.1)),
        const SizedBox(height: 4),
        Text('How disciplined do you want to be?', style: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 12.5)),
        const SizedBox(height: 28),
        ...locks.map((item) {
          final (type, label, desc) = item;
          final sel = lock == type;
          return GestureDetector(
            onTap: () => onLock(type),
            child: Container(
              width: double.infinity,
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: sel ? const Color(0x0F10B981) : AppColors.surface,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: sel ? const Color(0x4010B981) : AppColors.surfaceBorder),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(label, style: TextStyle(color: sel ? const Color(0xE634D399) : Colors.white.withOpacity(0.70), fontSize: 13.5, fontWeight: FontWeight.w500)),
                        const SizedBox(height: 4),
                        Text(desc, style: TextStyle(color: Colors.white.withOpacity(0.28), fontSize: 11, height: 1.5)),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Container(
                    width: 18, height: 18,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: sel ? const Color(0x2610B981) : Colors.transparent,
                      border: Border.all(color: sel ? AppColors.emerald : Colors.white.withOpacity(0.15), width: 2),
                    ),
                    child: sel ? const Icon(Icons.check, size: 10, color: AppColors.emeraldLight) : null,
                  ),
                ],
              ),
            ),
          );
        }),
        if (name.isNotEmpty && amount.isNotEmpty) ...[
          GlassCard(
            backgroundColor: AppColors.white03, borderColor: AppColors.white07,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('SUMMARY', style: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 9.5, letterSpacing: 2.2, fontWeight: FontWeight.w500)),
                const SizedBox(height: 12),
                _Row('Goal name', name),
                const SizedBox(height: 10),
                _Row('Target', '₹$amount'),
                const SizedBox(height: 10),
                _Row('Lock', lock),
              ],
            ),
          ),
        ],
        const SizedBox(height: 24),
      ],
    );
  }
}

class _Row extends StatelessWidget {
  final String label, value;
  const _Row(this.label, this.value);
  @override
  Widget build(BuildContext context) => Row(
    mainAxisAlignment: MainAxisAlignment.spaceBetween,
    children: [
      Text(label, style: TextStyle(color: Colors.white.withOpacity(0.35), fontSize: 12)),
      Text(value, style: TextStyle(color: Colors.white.withOpacity(0.75), fontSize: 12, fontWeight: FontWeight.w500)),
    ],
  );
}
