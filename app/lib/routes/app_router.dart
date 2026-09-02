import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../features/splash/splash_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/otp_screen.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/goals/goal_detail_screen.dart';
import '../features/goals/create_goal_screen.dart';
import '../features/deposit/deposit_screen.dart';
import '../features/deposit/withdrawal_screen.dart';
import '../features/profile/profile_screen.dart';
import '../models/api_models.dart';

class AppRoutes {
  static const splash = '/';
  static const login = '/login';
  static const otp = '/otp';
  static const dashboard = '/dashboard';
  static const goalDetail = '/goal-detail';
  static const createGoal = '/create-goal';
  static const deposit = '/deposit';
  static const withdrawal = '/withdrawal';
  static const profile = '/profile';
}

final router = GoRouter(
  initialLocation: AppRoutes.splash,
  routes: [
    GoRoute(
      path: AppRoutes.splash,
      pageBuilder: (_, s) => _fade(const SplashScreen()),
    ),
    GoRoute(
      path: AppRoutes.login,
      pageBuilder: (_, s) => _slide(const LoginScreen()),
    ),
    GoRoute(
      path: AppRoutes.otp,
      pageBuilder: (_, s) => _slide(const OtpScreen()),
    ),
    GoRoute(
      path: AppRoutes.dashboard,
      pageBuilder: (_, s) => _fade(const DashboardScreen()),
    ),
    GoRoute(
      path: AppRoutes.goalDetail,
      pageBuilder: (_, s) => _slide(GoalDetailScreen(goal: s.extra as GoalModel)),
    ),
    GoRoute(
      path: AppRoutes.createGoal,
      pageBuilder: (_, s) => _slide(const CreateGoalScreen()),
    ),
    GoRoute(
      path: AppRoutes.deposit,
      pageBuilder: (_, s) => _slide(DepositScreen(initialGoal: s.extra as GoalModel?)),
    ),
    GoRoute(
      path: AppRoutes.withdrawal,
      pageBuilder: (_, s) => _slide(WithdrawalScreen(initialGoal: s.extra as GoalModel?)),
    ),
    GoRoute(
      path: AppRoutes.profile,
      pageBuilder: (_, s) => _slide(const ProfileScreen()),
    ),
  ],
);

CustomTransitionPage<void> _slide(Widget child) => CustomTransitionPage(
      child: child,
      transitionsBuilder: (_, anim, __, child) => SlideTransition(
        position: Tween(begin: const Offset(1, 0), end: Offset.zero)
            .chain(CurveTween(curve: Curves.easeOutCubic))
            .animate(anim),
        child: child,
      ),
      transitionDuration: const Duration(milliseconds: 300),
    );

CustomTransitionPage<void> _fade(Widget child) => CustomTransitionPage(
      child: child,
      transitionsBuilder: (_, anim, __, child) =>
          FadeTransition(opacity: anim, child: child),
      transitionDuration: const Duration(milliseconds: 250),
    );
