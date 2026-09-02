import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../models/api_models.dart';
import '../../routes/app_router.dart';
import '../../services/providers.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/shared_widgets.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashAsync = ref.watch(dashboardProvider);
    final goalsAsync = ref.watch(goalsProvider);
    final txnsAsync = ref.watch(transactionsProvider);
    final profileAsync = ref.watch(userProfileProvider);

    final name = profileAsync.valueOrNull?.name ?? 'there';

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            Expanded(
              child: CustomScrollView(
                physics: const BouncingScrollPhysics(),
                slivers: [
                  SliverToBoxAdapter(child: _Header(name: name, ref: ref)),
                  SliverToBoxAdapter(
                    child: dashAsync.when(
                      data: (d) => _StatsSection(data: d),
                      loading: () => _StatsSection(data: null),
                      error: (e, _) => _StatsSection(data: null),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: goalsAsync.when(
                      data: (goals) => _GoalsSection(goals: goals, ref: ref),
                      loading: () => _GoalsShimmer(),
                      error: (e, _) => Padding(
                        padding: const EdgeInsets.all(20),
                        child: ErrorRetry(
                          message: 'Failed to load goals',
                          onRetry: () => ref.invalidate(goalsProvider),
                        ),
                      ),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: dashAsync.when(
                      data: (d) => _ChartSection(totalSaved: d.totalSaved),
                      loading: () => const SizedBox.shrink(),
                      error: (_, __) => const SizedBox.shrink(),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: txnsAsync.when(
                      data: (txns) => _TransactionsSection(txns: txns),
                      loading: () => const _LoadingCard(),
                      error: (e, _) => const SizedBox.shrink(),
                    ),
                  ),
                  const SliverToBoxAdapter(child: SizedBox(height: 12)),
                ],
              ),
            ),
            const BottomNav(current: NavTab.home),
          ],
        ),
      ),
    );
  }
}

// ── Header ────────────────────────────────────────────────────────────────

class _Header extends StatelessWidget {
  final String name;
  final WidgetRef ref;
  const _Header({required this.name, required this.ref});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Good morning, $name',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontFamily: 'Georgia',
                        fontWeight: FontWeight.w400)),
                const SizedBox(height: 4),
                Text('Keep going. Your future self is watching.',
                    style: TextStyle(
                        color: Colors.white.withOpacity(0.28),
                        fontSize: 11,
                        letterSpacing: 0.3)),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Stack(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: AppColors.white05,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.white07),
                ),
                child: const Icon(Icons.notifications_outlined,
                    size: 15, color: AppColors.white40),
              ),
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  width: 6,
                  height: 6,
                  decoration: const BoxDecoration(
                      color: AppColors.emerald, shape: BoxShape.circle),
                ),
              ),
            ],
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: () => context.go(AppRoutes.profile),
            child: Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                    color: Colors.white.withOpacity(0.12), width: 1.5),
              ),
              child: ClipOval(
                child: ref.watch(userProfileProvider).maybeWhen(
                      data: (u) => u.profilePicture != null
                          ? Image.network(u.profilePicture!, fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) => _avatar())
                          : _avatar(),
                      orElse: _avatar,
                    ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _avatar() => const Icon(Icons.person, color: AppColors.white40, size: 18);
}

// ── Stats ─────────────────────────────────────────────────────────────────

class _StatsSection extends StatelessWidget {
  final DashboardData? data;
  const _StatsSection({this.data});

  @override
  Widget build(BuildContext context) {
    final saved = data?.totalSaved ?? 0;
    final streak = data?.currentStreak ?? 0;
    final active = data?.activeGoalsCount ?? 0;

    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      child: Column(
        children: [
          GlassCard(
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('TOTAL SAVED',
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.35),
                              fontSize: 10,
                              letterSpacing: 1.8,
                              fontWeight: FontWeight.w500)),
                      const SizedBox(height: 6),
                      Text('₹${saved.toStringAsFixed(0)}',
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 30,
                              fontWeight: FontWeight.w600,
                              height: 1)),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          const Icon(Icons.trending_up,
                              size: 11, color: AppColors.emeraldLight),
                          const SizedBox(width: 6),
                          const Text('+12.4%',
                              style: TextStyle(
                                  color: AppColors.emeraldLight,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w500)),
                          const SizedBox(width: 6),
                          Text('vs last month',
                              style: TextStyle(
                                  color: Colors.white.withOpacity(0.22),
                                  fontSize: 10)),
                        ],
                      ),
                    ],
                  ),
                ),
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: const Color(0x1410B981),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0x2610B981)),
                  ),
                  child: const Icon(Icons.account_balance_wallet_outlined,
                      size: 18, color: Color(0xCC34D399)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('ACTIVE GOALS',
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.35),
                              fontSize: 10,
                              letterSpacing: 1.8,
                              fontWeight: FontWeight.w500)),
                      const SizedBox(height: 8),
                      Text('$active',
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 28,
                              fontWeight: FontWeight.w600,
                              height: 1)),
                      const SizedBox(height: 6),
                      Text('${data?.completedGoalsCount ?? 0} completed',
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.25),
                              fontSize: 10)),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('STREAK',
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.35),
                              fontSize: 10,
                              letterSpacing: 1.8,
                              fontWeight: FontWeight.w500)),
                      const SizedBox(height: 8),
                      RichText(
                        text: TextSpan(
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 28,
                              fontWeight: FontWeight.w600,
                              height: 1),
                          children: [
                            TextSpan(text: '$streak'),
                            TextSpan(
                                text: 'd',
                                style: TextStyle(
                                    color: Colors.white.withOpacity(0.40),
                                    fontSize: 14)),
                          ],
                        ),
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          const Icon(Icons.local_fire_department,
                              size: 11, color: Color(0xCCFBBF24)),
                          const SizedBox(width: 4),
                          Text('Keep it up!',
                              style: const TextStyle(
                                  color: Color(0xFF7A6030),
                                  fontSize: 10)),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Goals carousel ────────────────────────────────────────────────────────

class _GoalsSection extends StatelessWidget {
  final List<GoalModel> goals;
  final WidgetRef ref;
  const _GoalsSection({required this.goals, required this.ref});

  @override
  Widget build(BuildContext context) {
    if (goals.isEmpty) {
      return Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
        child: GlassCard(
          child: Column(
            children: [
              Text('No active goals yet',
                  style: TextStyle(
                      color: Colors.white.withOpacity(0.40), fontSize: 13)),
              const SizedBox(height: 12),
              GestureDetector(
                onTap: () => context.go(AppRoutes.createGoal),
                child: Text('Create your first goal →',
                    style: const TextStyle(
                        color: AppColors.emeraldLight, fontSize: 12)),
              ),
            ],
          ),
        ),
      );
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Your Goals',
                  style: TextStyle(
                      color: AppColors.white80,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      letterSpacing: 0.3)),
              Row(
                children: [
                  GestureDetector(
                    onTap: () => context.go(AppRoutes.createGoal),
                    child: const Text('+ New',
                        style: TextStyle(
                            color: Color(0x9934D399),
                            fontSize: 11,
                            fontWeight: FontWeight.w500)),
                  ),
                ],
              ),
            ],
          ),
        ),
        SizedBox(
          height: 212,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            physics: const BouncingScrollPhysics(),
            padding: const EdgeInsets.only(left: 20, right: 8),
            itemCount: goals.length,
            itemBuilder: (_, i) => _GoalCard(goal: goals[i]),
          ),
        ),
        const SizedBox(height: 20),
      ],
    );
  }
}

class _GoalCard extends StatelessWidget {
  final GoalModel goal;
  const _GoalCard({required this.goal});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.go(AppRoutes.goalDetail, extra: goal),
      child: Container(
        width: 160,
        margin: const EdgeInsets.only(right: 12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppColors.surfaceBorder),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: 92,
              child: Stack(fit: StackFit.expand, children: [
                Image.network(goal.imageUrlOrFallback,
                    fit: BoxFit.cover,
                    opacity: const AlwaysStoppedAnimation(0.75),
                    errorBuilder: (_, __, ___) =>
                        Container(color: AppColors.white05)),
                Container(color: const Color(0x73141619)),
                Positioned(
                  top: 8,
                  left: 8,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(100),
                    ),
                    child: Text(goal.category,
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.45),
                            fontSize: 8.5,
                            fontWeight: FontWeight.w500)),
                  ),
                ),
              ]),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(goal.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                          color: Colors.white.withOpacity(0.85),
                          fontSize: 11.5,
                          fontWeight: FontWeight.w500)),
                  const SizedBox(height: 4),
                  Text(
                      '₹${goal.savedAmount.toStringAsFixed(0)} / ₹${goal.targetAmount.toStringAsFixed(0)}',
                      style: const TextStyle(
                          color: AppColors.white30,
                          fontSize: 9.5)),
                  const SizedBox(height: 8),
                  AppProgressBar(value: goal.progressPercentage),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      LockBadge(lockType: goal.lockType),
                      Text('${goal.progressPercentage.toStringAsFixed(0)}%',
                          style: const TextStyle(
                              color: AppColors.white30, fontSize: 10)),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GoalsShimmer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 212 + 44,
      child: Center(
        child: CircularProgressIndicator(
          strokeWidth: 1.5,
          color: AppColors.emerald.withOpacity(0.4),
        ),
      ),
    );
  }
}

// ── Chart section ─────────────────────────────────────────────────────────

class _ChartSection extends StatelessWidget {
  final double totalSaved;
  const _ChartSection({required this.totalSaved});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Savings Overview',
                    style: TextStyle(
                        color: AppColors.white80,
                        fontSize: 13,
                        fontWeight: FontWeight.w500)),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                      border: Border.all(color: AppColors.white07),
                      borderRadius: BorderRadius.circular(8)),
                  child: const Text('This Month',
                      style: TextStyle(
                          color: AppColors.white25, fontSize: 10)),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text('₹${totalSaved.toStringAsFixed(0)}',
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 22,
                    fontWeight: FontWeight.w600,
                    height: 1)),
            const SizedBox(height: 4),
            Text('Total saved',
                style: TextStyle(
                    color: Colors.white.withOpacity(0.25), fontSize: 10)),
            const SizedBox(height: 16),
            SavingsChart(totalSaved: totalSaved),
          ],
        ),
      ),
    );
  }
}

// ── Transactions ──────────────────────────────────────────────────────────

class _TransactionsSection extends StatelessWidget {
  final List<TxnModel> txns;
  const _TransactionsSection({required this.txns});

  @override
  Widget build(BuildContext context) {
    if (txns.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Recent Transactions',
              style: TextStyle(
                  color: AppColors.white80,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  letterSpacing: 0.3)),
          const SizedBox(height: 12),
          GlassCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: txns
                  .take(5)
                  .toList()
                  .asMap()
                  .entries
                  .map((e) => _TxnRow(txn: e.value, isLast: e.key == txns.length - 1 || e.key == 4))
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }
}

class _TxnRow extends StatelessWidget {
  final TxnModel txn;
  final bool isLast;
  const _TxnRow({required this.txn, required this.isLast});

  @override
  Widget build(BuildContext context) {
    final isDeposit = txn.transactionType == 'DEPOSIT';
    final iconBg =
        isDeposit ? const Color(0x1410B981) : const Color(0x14EF4444);
    final iconColor =
        isDeposit ? const Color(0xCC34D399) : const Color(0xCCEF4444);
    final icon = isDeposit ? Icons.arrow_downward : Icons.arrow_upward;
    final amountColor =
        isDeposit ? AppColors.emeraldLight : const Color(0xCCEF4444);
    final amountText = isDeposit
        ? '+₹${txn.amount.toStringAsFixed(0)}'
        : '-₹${txn.amount.toStringAsFixed(0)}';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        border: isLast
            ? null
            : const Border(
                bottom: BorderSide(color: Color(0x0DFFFFFF))),
      ),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
                color: iconBg, borderRadius: BorderRadius.circular(10)),
            child: Icon(icon, size: 13, color: iconColor),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                    isDeposit ? 'Money Added' : 'Withdrawal',
                    style: const TextStyle(
                        color: AppColors.white80,
                        fontSize: 12,
                        fontWeight: FontWeight.w500)),
                Text(txn.referenceType ?? txn.transactionType,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                        color: Colors.white.withOpacity(0.28),
                        fontSize: 10)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(amountText,
                  style: TextStyle(
                      color: amountColor, fontSize: 11.5, fontWeight: FontWeight.w500)),
              Text(txn.formattedDate,
                  style: const TextStyle(
                      color: AppColors.white20, fontSize: 9.5)),
            ],
          ),
        ],
      ),
    );
  }
}

class _LoadingCard extends StatelessWidget {
  const _LoadingCard();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(20),
      child: Center(
        child: SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(
            strokeWidth: 1.5,
            color: AppColors.emerald,
          ),
        ),
      ),
    );
  }
}
