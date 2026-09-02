import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../core/theme/app_theme.dart';
import '../routes/app_router.dart';

enum NavTab { home, goals, add, wallet, profile }

class BottomNav extends StatelessWidget {
  final NavTab current;

  const BottomNav({super.key, required this.current});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 72,
      decoration: const BoxDecoration(
        color: Color(0xF20C0E11),
        border: Border(
          top: BorderSide(color: Color(0x0FFFFFFF)),
        ),
      ),
      child: Row(
        children: [
          _NavItem(
            icon: Icons.home_outlined,
            label: 'Home',
            active: current == NavTab.home,
            onTap: () => context.go(AppRoutes.dashboard),
          ),
          _NavItem(
            icon: Icons.track_changes_outlined,
            label: 'Goals',
            active: current == NavTab.goals,
            onTap: () => context.go(AppRoutes.goalDetail),
          ),
          _FabItem(onTap: () => context.go(AppRoutes.createGoal)),
          _NavItem(
            icon: Icons.account_balance_wallet_outlined,
            label: 'Add',
            active: current == NavTab.wallet,
            onTap: () => context.go(AppRoutes.deposit),
          ),
          _NavItem(
            icon: Icons.person_outline,
            label: 'Profile',
            active: current == NavTab.profile,
            onTap: () => context.go(AppRoutes.profile),
          ),
        ],
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool active;
  final VoidCallback onTap;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color = active ? AppColors.emeraldLight : AppColors.white25;
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 21, color: color),
            const SizedBox(height: 3),
            Text(
              label,
              style: TextStyle(
                color: color,
                fontSize: 9.5,
                fontWeight: FontWeight.w500,
                letterSpacing: 0.3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FabItem extends StatelessWidget {
  final VoidCallback onTap;

  const _FabItem({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Center(
          child: Transform.translate(
            offset: const Offset(0, -6),
            child: Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: const Color(0x1A10B981),
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0x3310B981)),
              ),
              child: const Icon(
                Icons.add,
                color: Color(0xCC34D399),
                size: 19,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
