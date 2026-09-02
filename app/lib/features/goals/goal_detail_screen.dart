import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../models/api_models.dart';
import '../../routes/app_router.dart';
import '../../services/providers.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/shared_widgets.dart';

class GoalDetailScreen extends ConsumerStatefulWidget {
  final GoalModel goal;
  const GoalDetailScreen({super.key, required this.goal});

  @override
  ConsumerState<GoalDetailScreen> createState() => _GoalDetailState();
}

class _GoalDetailState extends ConsumerState<GoalDetailScreen> {
  late GoalModel _goal;
  bool _loadingGoal = false;

  @override
  void initState() {
    super.initState();
    _goal = widget.goal;
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() => _loadingGoal = true);
    try {
      final fresh = await ref.read(goalRepoProvider).getGoal(_goal.id);
      if (mounted) setState(() => _goal = fresh);
    } catch (_) {}
    if (mounted) setState(() => _loadingGoal = false);
  }

  @override
  Widget build(BuildContext context) {
    final txnsAsync = ref.watch(transactionsProvider);

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: Column(
        children: [
          _HeroHeader(goal: _goal),
          Expanded(
            child: RefreshIndicator(
              color: AppColors.emerald,
              backgroundColor: AppColors.bg,
              onRefresh: _refresh,
              child: CustomScrollView(
                physics: const AlwaysScrollableScrollPhysics(
                    parent: BouncingScrollPhysics()),
                slivers: [
                  SliverToBoxAdapter(child: _ProgressCard(goal: _goal)),
                  SliverToBoxAdapter(child: _StatsRow(goal: _goal)),
                  SliverToBoxAdapter(child: _Actions(goal: _goal)),
                  SliverToBoxAdapter(
                    child: txnsAsync.when(
                      data: (all) {
                        final filtered =
                            all.where((t) => t.goalId == _goal.id).toList();
                        return _RecentActivity(txns: filtered);
                      },
                      loading: () => const SizedBox.shrink(),
                      error: (_, __) => const SizedBox.shrink(),
                    ),
                  ),
                  const SliverToBoxAdapter(child: SizedBox(height: 32)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _HeroHeader extends StatelessWidget {
  final GoalModel goal;
  const _HeroHeader({required this.goal});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 210,
      child: Stack(fit: StackFit.expand, children: [
        Image.network(goal.imageUrlOrFallback,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Container(color: AppColors.white05)),
        Container(color: const Color(0xA6141619)),
        SafeArea(
          bottom: false,
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
                child: GestureDetector(
                  onTap: () => context.go(AppRoutes.dashboard),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.35),
                        shape: BoxShape.circle,
                        border: Border.all(
                            color: Colors.white.withOpacity(0.10)),
                      ),
                      child: const Icon(Icons.chevron_left,
                          color: Color(0xA6FFFFFF), size: 20),
                    ),
                  ),
                ),
              ),
              const Spacer(),
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(goal.category.toUpperCase(),
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.40),
                              fontSize: 9,
                              letterSpacing: 3.5,
                              fontWeight: FontWeight.w500)),
                      const SizedBox(height: 4),
                      Text(goal.title,
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 24,
                              fontFamily: 'Georgia',
                              fontWeight: FontWeight.w400)),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ]),
    );
  }
}

class _ProgressCard extends StatelessWidget {
  final GoalModel goal;
  const _ProgressCard({required this.goal});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: GlassCard(
        child: Column(
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('SAVED SO FAR',
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.30),
                            fontSize: 10,
                            letterSpacing: 1.8,
                            fontWeight: FontWeight.w500)),
                    const SizedBox(height: 4),
                    Text('₹${goal.savedAmount.toStringAsFixed(0)}',
                        style: const TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.w600,
                            height: 1)),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('TARGET',
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.30),
                            fontSize: 10,
                            letterSpacing: 1.8,
                            fontWeight: FontWeight.w500)),
                    const SizedBox(height: 4),
                    Text('₹${goal.targetAmount.toStringAsFixed(0)}',
                        style: const TextStyle(
                            color: AppColors.white50, fontSize: 17)),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            AppProgressBar(value: goal.progressPercentage),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('${goal.progressPercentage.toStringAsFixed(0)}% complete',
                    style: const TextStyle(
                        color: AppColors.emeraldLight, fontSize: 11, fontWeight: FontWeight.w500)),
                Text('₹${goal.remainingAmount.toStringAsFixed(0)} remaining',
                    style: const TextStyle(color: AppColors.white30, fontSize: 11)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatsRow extends StatelessWidget {
  final GoalModel goal;
  const _StatsRow({required this.goal});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 0),
      child: Row(
        children: [
          Expanded(child: _Mini('Days Left', '${goal.daysLeft}', 'd')),
          const SizedBox(width: 10),
          Expanded(
              child: _Mini('Daily Need', '₹${goal.dailyNeed}', '/d')),
          const SizedBox(width: 10),
          Expanded(
            child: GlassCard(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  Text('LOCK',
                      style: TextStyle(
                          color: Colors.white.withOpacity(0.28),
                          fontSize: 9,
                          letterSpacing: 2.2,
                          fontWeight: FontWeight.w500)),
                  const SizedBox(height: 8),
                  LockBadge(lockType: goal.lockType),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Mini extends StatelessWidget {
  final String label, value, unit;
  const _Mini(this.label, this.value, this.unit);

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          Text(label.toUpperCase(),
              textAlign: TextAlign.center,
              style: TextStyle(
                  color: Colors.white.withOpacity(0.28),
                  fontSize: 9,
                  letterSpacing: 2.2,
                  fontWeight: FontWeight.w500)),
          const SizedBox(height: 6),
          RichText(
            text: TextSpan(
              style: const TextStyle(
                  color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500),
              children: [
                TextSpan(text: value),
                TextSpan(
                    text: unit,
                    style: const TextStyle(
                        color: AppColors.white30, fontSize: 10)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Actions extends StatelessWidget {
  final GoalModel goal;
  const _Actions({required this.goal});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => context.go(AppRoutes.deposit, extra: goal),
              child: Container(
                height: 50,
                decoration: BoxDecoration(
                  color: const Color(0x1410B981),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: const Color(0x3310B981)),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.arrow_downward,
                        size: 15, color: Color(0xE634D399)),
                    SizedBox(width: 8),
                    Text('Add Money',
                        style: TextStyle(
                            color: Color(0xE634D399),
                            fontSize: 12.5,
                            fontWeight: FontWeight.w500)),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: GestureDetector(
              onTap: () => context.go(AppRoutes.withdrawal, extra: goal),
              child: Container(
                height: 50,
                decoration: BoxDecoration(
                  color: AppColors.white04,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: AppColors.white07),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.arrow_upward,
                        size: 15, color: AppColors.white50),
                    SizedBox(width: 8),
                    Text('Withdraw',
                        style: TextStyle(
                            color: AppColors.white50,
                            fontSize: 12.5,
                            fontWeight: FontWeight.w500)),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RecentActivity extends StatelessWidget {
  final List<TxnModel> txns;
  const _RecentActivity({required this.txns});

  @override
  Widget build(BuildContext context) {
    if (txns.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('RECENT ACTIVITY',
              style: TextStyle(
                  color: Colors.white.withOpacity(0.25),
                  fontSize: 9.5,
                  letterSpacing: 2.2,
                  fontWeight: FontWeight.w500)),
          const SizedBox(height: 12),
          GlassCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: txns.take(5).toList().asMap().entries.map((e) {
                final t = e.value;
                final isLast = e.key == txns.length - 1 || e.key == 4;
                final isDeposit = t.transactionType == 'DEPOSIT';
                return Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 14),
                  decoration: BoxDecoration(
                    border: isLast
                        ? null
                        : const Border(
                            bottom:
                                BorderSide(color: Color(0x0DFFFFFF))),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 28,
                        height: 28,
                        decoration: BoxDecoration(
                          color: isDeposit
                              ? const Color(0x1410B981)
                              : const Color(0x14EF4444),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(
                          isDeposit
                              ? Icons.arrow_downward
                              : Icons.arrow_upward,
                          size: 12,
                          color: isDeposit
                              ? const Color(0xB334D399)
                              : const Color(0xB3EF4444),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                                isDeposit
                                    ? 'Money Added'
                                    : 'Withdrawal',
                                style: TextStyle(
                                    color:
                                        Colors.white.withOpacity(0.75),
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.w500)),
                            Text(t.formattedDate,
                                style: const TextStyle(
                                    color: AppColors.white25,
                                    fontSize: 9.5)),
                          ],
                        ),
                      ),
                      Text(
                        isDeposit
                            ? '+₹${t.amount.toStringAsFixed(0)}'
                            : '-₹${t.amount.toStringAsFixed(0)}',
                        style: TextStyle(
                          color: isDeposit
                              ? AppColors.emeraldLight
                              : const Color(0xCCEF4444),
                          fontSize: 11.5,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}
