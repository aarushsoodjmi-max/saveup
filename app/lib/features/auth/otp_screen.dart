import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../routes/app_router.dart';
import '../../services/providers.dart';
import '../../services/api_client.dart';
import '../../widgets/shared_widgets.dart';
import '../../widgets/glass_button.dart';
import '../../widgets/otp_field.dart';

class OtpScreen extends ConsumerStatefulWidget {
  const OtpScreen({super.key});

  @override
  ConsumerState<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends ConsumerState<OtpScreen> {
  int _timer = 28;
  Timer? _countdown;
  String _otp = '';
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _countdown?.cancel();
    setState(() => _timer = 28);
    _countdown = Timer.periodic(const Duration(seconds: 1), (t) {
      if (_timer <= 0) {
        t.cancel();
      } else {
        setState(() => _timer--);
      }
    });
  }

  @override
  void dispose() {
    _countdown?.cancel();
    super.dispose();
  }

  Future<void> _resend() async {
    final phone = ref.read(phoneProvider);
    try {
      final resp = await ref.read(authRepoProvider).sendOtp(phone);
      ref.read(debugOtpProvider.notifier).state = resp.debugOtp;
      _startTimer();
    } catch (_) {}
  }

  Future<void> _verify() async {
    final phone = ref.read(phoneProvider);
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authRepoProvider).verifyOtp(phone, _otp);
      if (!mounted) return;
      context.go(AppRoutes.dashboard);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = 'Verification failed. Try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final phone = ref.watch(phoneProvider);
    final debugOtp = ref.watch(debugOtpProvider);

    return Scaffold(
      backgroundColor: AppColors.bg,
      resizeToAvoidBottomInset: true,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(28, 16, 28, 48),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              GestureDetector(
                onTap: () => context.go(AppRoutes.login),
                child: Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: AppColors.white05,
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.white07),
                  ),
                  child: const Icon(Icons.chevron_left,
                      color: AppColors.white50, size: 20),
                ),
              ),
              const SizedBox(height: 36),
              const Text('Verify.',
                  style: TextStyle(
                      color: Colors.white,
                      fontSize: 42,
                      fontFamily: 'Georgia',
                      fontWeight: FontWeight.w400,
                      height: 1.1,
                      letterSpacing: -0.5)),
              const SizedBox(height: 6),
              RichText(
                text: TextSpan(
                  style: const TextStyle(fontSize: 13),
                  children: [
                    TextSpan(
                        text: 'OTP sent to ',
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.30))),
                    TextSpan(
                        text: phone,
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.55))),
                  ],
                ),
              ),

              // Dev helper banner
              if (debugOtp != null) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0x1AFBBF24),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0x4DFBBF24)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.bug_report_outlined,
                          size: 14, color: Color(0xCCFBBF24)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Debug OTP: $debugOtp',
                          style: const TextStyle(
                              color: Color(0xCCFBBF24),
                              fontFamily: 'Courier',
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 3),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 36),
              OtpField(
                onCompleted: (v) => setState(() => _otp = v),
                onChanged: () => setState(() => _otp = ''),
              ),
              const SizedBox(height: 28),
              Center(
                child: _timer > 0
                    ? RichText(
                        text: TextSpan(
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.25),
                              fontSize: 12),
                          children: [
                            const TextSpan(text: 'Resend OTP in '),
                            TextSpan(
                                text: '${_timer}s',
                                style: TextStyle(
                                    color: Colors.white.withOpacity(0.45))),
                          ],
                        ),
                      )
                    : GestureDetector(
                        onTap: _resend,
                        child: const Text('Resend OTP',
                            style: TextStyle(
                                color: Color(0xCB34D399), fontSize: 12)),
                      ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 20),
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
              const SizedBox(height: 36),
              GlassButton(
                label: 'Verify & Continue',
                enabled: _otp.length == 6 && !_loading,
                loading: _loading,
                onTap: _otp.length == 6 ? _verify : null,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
