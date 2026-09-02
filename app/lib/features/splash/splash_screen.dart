import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../routes/app_router.dart';
import '../../services/providers.dart';
import '../../widgets/shared_widgets.dart';
import '../../widgets/glass_button.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    await Future.delayed(const Duration(milliseconds: 900));
    if (!mounted) return;
    final loggedIn = await ref.read(isLoggedInProvider.future);
    if (!mounted) return;
    if (loggedIn) {
      context.go(AppRoutes.dashboard);
    } else {
      setState(() => _ready = true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: Stack(
        children: [
          Center(
            child: Container(
              width: 280,
              height: 280,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF064E3B).withOpacity(0.18),
              ),
            ),
          ),
          AnimatedOpacity(
            opacity: _ready ? 1.0 : 0.0,
            duration: const Duration(milliseconds: 350),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(32, 0, 32, 48),
              child: Column(
                children: [
                  Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SaveUpMark(size: 64),
                        const SizedBox(height: 24),
                        const Text('SaveUp',
                            style: TextStyle(
                                color: Colors.white,
                                fontSize: 52,
                                fontFamily: 'Georgia',
                                fontWeight: FontWeight.w400,
                                height: 1,
                                letterSpacing: -1)),
                        const SizedBox(height: 12),
                        Text('SAVE WITH INTENTION',
                            style: TextStyle(
                                color: Colors.white.withOpacity(0.28),
                                fontSize: 11,
                                fontWeight: FontWeight.w500,
                                letterSpacing: 4.5)),
                        const SizedBox(height: 20),
                        Container(width: 64, height: 1, color: AppColors.white07),
                        const SizedBox(height: 20),
                        Text(
                            'Discipline your spending.\nBuild your future, one goal at a time.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                                color: Colors.white.withOpacity(0.20),
                                fontSize: 12,
                                height: 1.6)),
                      ],
                    ),
                  ),
                  Column(
                    children: [
                      GlassButton(
                        label: 'Get Started',
                        onTap: () => context.go(AppRoutes.login),
                      ),
                      const SizedBox(height: 12),
                      GestureDetector(
                        onTap: () => context.go(AppRoutes.login),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          child: RichText(
                            text: TextSpan(
                              style: const TextStyle(fontSize: 13),
                              children: [
                                TextSpan(
                                    text: 'Already a member? ',
                                    style: TextStyle(
                                        color:
                                            Colors.white.withOpacity(0.30))),
                                TextSpan(
                                    text: 'Sign in',
                                    style: TextStyle(
                                        color:
                                            Colors.white.withOpacity(0.50))),
                              ],
                            ),
                          ),
                        ),
                      ),
                      Text(
                          'Protected by 256-bit encryption. Your data is never shared.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.15),
                              fontSize: 10,
                              height: 1.5)),
                    ],
                  ),
                ],
              ),
            ),
          ),
          if (!_ready)
            const Center(
              child: SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(
                  strokeWidth: 1.5,
                  color: AppColors.emerald,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
