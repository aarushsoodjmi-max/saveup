import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../routes/app_router.dart';
import '../../services/providers.dart';
import '../../services/api_client.dart';
import '../../widgets/shared_widgets.dart';
import '../../widgets/glass_button.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _ctrl = TextEditingController();
  bool _loading = false;
  String? _error;

  bool get _ready => _ctrl.text.replaceAll(' ', '').length == 10;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _sendOtp() async {
    final raw = _ctrl.text.replaceAll(' ', '');
    final phone = '+91$raw';
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final resp = await ref.read(authRepoProvider).sendOtp(phone);
      if (!mounted) return;
      ref.read(phoneProvider.notifier).state = phone;
      ref.read(debugOtpProvider.notifier).state = resp.debugOtp;
      context.go(AppRoutes.otp);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = 'Could not connect. Check your network.');
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
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(28, 16, 28, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SaveUpMark(size: 28),
                    const SizedBox(height: 32),
                    const Text('Welcome.',
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 42,
                            fontFamily: 'Georgia',
                            fontWeight: FontWeight.w400,
                            height: 1.1,
                            letterSpacing: -0.5)),
                    const SizedBox(height: 6),
                    Text('Your wealth, disciplined.',
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.30),
                            fontSize: 13)),
                    const SizedBox(height: 40),
                    Text('MOBILE NUMBER',
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.30),
                            fontSize: 10,
                            fontWeight: FontWeight.w500,
                            letterSpacing: 3.5)),
                    const SizedBox(height: 10),
                    AnimatedBuilder(
                      animation: _ctrl,
                      builder: (_, __) => Container(
                        decoration: BoxDecoration(
                          color: AppColors.white04,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(
                            color: _ready
                                ? const Color(0x4010B981)
                                : AppColors.white07,
                          ),
                        ),
                        child: Row(
                          children: [
                            Padding(
                              padding:
                                  const EdgeInsets.fromLTRB(16, 0, 12, 0),
                              child: Row(
                                children: [
                                  _IndiaFlag(),
                                  const SizedBox(width: 8),
                                  Text('+91',
                                      style: TextStyle(
                                          color: Colors.white.withOpacity(0.50),
                                          fontSize: 13)),
                                  const SizedBox(width: 4),
                                  Icon(Icons.chevron_right,
                                      size: 13,
                                      color: Colors.white.withOpacity(0.25)),
                                ],
                              ),
                            ),
                            Container(
                                width: 1,
                                height: 20,
                                color: AppColors.white07),
                            Expanded(
                              child: TextField(
                                controller: _ctrl,
                                onChanged: (_) => setState(() {}),
                                keyboardType: TextInputType.phone,
                                inputFormatters: [
                                  FilteringTextInputFormatter.digitsOnly,
                                  LengthLimitingTextInputFormatter(10),
                                ],
                                style: const TextStyle(
                                    color: Colors.white, fontSize: 15,
                                    letterSpacing: 2),
                                decoration: InputDecoration(
                                  hintText: '98765 43210',
                                  hintStyle: TextStyle(
                                      color: Colors.white.withOpacity(0.15),
                                      letterSpacing: 2),
                                  border: InputBorder.none,
                                  contentPadding: const EdgeInsets.symmetric(
                                      horizontal: 12, vertical: 16),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.all(12),
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
                    const SizedBox(height: 12),
                    Text('We will send a 6-digit OTP to verify your number.',
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.20),
                            fontSize: 11,
                            height: 1.5)),
                    const SizedBox(height: 32),
                    AnimatedBuilder(
                      animation: _ctrl,
                      builder: (_, __) => GlassButton(
                        label: 'Continue',
                        enabled: _ready && !_loading,
                        loading: _loading,
                        onTap: _ready ? _sendOtp : null,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(28, 16, 28, 24),
              child: Text(
                  'By continuing you agree to our Terms of Service\nand Privacy Policy',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                      color: Colors.white.withOpacity(0.15),
                      fontSize: 10,
                      height: 1.6)),
            ),
          ],
        ),
      ),
    );
  }
}

class _IndiaFlag extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(2),
      child: SizedBox(
        width: 20,
        height: 14,
        child: Column(children: [
          Expanded(child: Container(color: const Color(0xFFFF9933))),
          Expanded(
            child: Container(
              color: Colors.white,
              child: Center(
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                        color: const Color(0xFF000080).withOpacity(0.4),
                        width: 0.5),
                  ),
                ),
              ),
            ),
          ),
          Expanded(child: Container(color: const Color(0xFF138808))),
        ]),
      ),
    );
  }
}
