import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../core/theme/app_theme.dart';
import '../routes/app_router.dart';
import 'dart:math' as math;

// ── Bottom Navigation ─────────────────────────────────────────────────────

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
        border: Border(top: BorderSide(color: Color(0x0FFFFFFF))),
      ),
      child: Row(
        children: [
          _Item(Icons.home_outlined, 'Home', current == NavTab.home,
              () => context.go(AppRoutes.dashboard)),
          _Item(Icons.track_changes_outlined, 'Goals', current == NavTab.goals,
              () => context.go(AppRoutes.goalDetail)),
          _Fab(() => context.go(AppRoutes.createGoal)),
          _Item(Icons.account_balance_wallet_outlined, 'Add',
              current == NavTab.wallet, () => context.go(AppRoutes.deposit)),
          _Item(Icons.person_outline, 'Profile', current == NavTab.profile,
              () => context.go(AppRoutes.profile)),
        ],
      ),
    );
  }
}

class _Item extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool active;
  final VoidCallback onTap;
  const _Item(this.icon, this.label, this.active, this.onTap);

  @override
  Widget build(BuildContext context) {
    final c = active ? AppColors.emeraldLight : AppColors.white25;
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 21, color: c),
            const SizedBox(height: 3),
            Text(label,
                style: TextStyle(
                    color: c,
                    fontSize: 9.5,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0.3)),
          ],
        ),
      ),
    );
  }
}

class _Fab extends StatelessWidget {
  final VoidCallback onTap;
  const _Fab(this.onTap);

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
              child: const Icon(Icons.add, color: Color(0xCC34D399), size: 19),
            ),
          ),
        ),
      ),
    );
  }
}

// ── Progress bar ──────────────────────────────────────────────────────────

class AppProgressBar extends StatelessWidget {
  final double value; // 0–100
  final double height;
  const AppProgressBar({super.key, required this.value, this.height = 3});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(100),
      child: LinearProgressIndicator(
        value: value.clamp(0, 100) / 100,
        backgroundColor: AppColors.white07,
        valueColor: const AlwaysStoppedAnimation(AppColors.emerald),
        minHeight: height,
      ),
    );
  }
}

// ── Lock badge ────────────────────────────────────────────────────────────

class LockBadge extends StatelessWidget {
  final String lockType;
  const LockBadge({super.key, required this.lockType});

  @override
  Widget build(BuildContext context) {
    Color bg, border, fg;
    String label;
    switch (lockType) {
      case 'HARD':
        bg = Colors.transparent;
        border = AppColors.white15;
        fg = AppColors.white40;
        label = 'Hard Lock';
        break;
      case 'MEDIUM':
        bg = const Color(0x14FBBF24);
        border = const Color(0x4DFBBF24);
        fg = const Color(0xCCFBBF24);
        label = 'Medium Lock';
        break;
      default:
        bg = const Color(0x1210B981);
        border = const Color(0x4010B981);
        fg = const Color(0xCC34D399);
        label = 'Easy Lock';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(100),
        border: Border.all(color: border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.lock_outline, size: 8, color: fg),
          const SizedBox(width: 4),
          Text(label,
              style: TextStyle(
                  color: fg,
                  fontSize: 9,
                  fontWeight: FontWeight.w500,
                  letterSpacing: 0.5)),
        ],
      ),
    );
  }
}

// ── Screen header ─────────────────────────────────────────────────────────

class ScreenHeader extends StatelessWidget {
  final String title;
  final VoidCallback? onBack;
  const ScreenHeader({super.key, required this.title, this.onBack});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 4, 20, 12),
      child: Row(
        children: [
          GestureDetector(
            onTap: onBack ?? () => context.pop(),
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
          const SizedBox(width: 12),
          Text(title,
              style: const TextStyle(
                  color: AppColors.white80,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  letterSpacing: 0.4)),
        ],
      ),
    );
  }
}

// ── Savings sparkline ─────────────────────────────────────────────────────

class SavingsChart extends StatelessWidget {
  final double totalSaved;
  const SavingsChart({super.key, this.totalSaved = 0});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          height: 78,
          child: CustomPaint(
            painter: _ChartPainter(totalSaved),
            size: const Size(double.infinity, 78),
          ),
        ),
        const SizedBox(height: 6),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: ['1 May', '8', '15', '22', '29 May']
              .map((l) => Text(l,
                  style: const TextStyle(
                      color: AppColors.white20,
                      fontSize: 9,
                      fontFamily: 'Courier')))
              .toList(),
        ),
      ],
    );
  }
}

class _ChartPainter extends CustomPainter {
  final double totalSaved;
  _ChartPainter(this.totalSaved);

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final peak = totalSaved <= 0 ? 1.0 : totalSaved;
    final rawPts = [0.18, 0.28, 0.38, 0.50, 0.62, 0.74, 0.88, 1.0];
    final pts = List.generate(rawPts.length, (i) {
      final x = (i / (rawPts.length - 1)) * w;
      final y = h - rawPts[i] * h * 0.92;
      return Offset(x, y);
    });

    final area = Path()..moveTo(pts[0].dx, pts[0].dy);
    for (final p in pts.skip(1)) area.lineTo(p.dx, p.dy);
    area..lineTo(w, h)..lineTo(0, h)..close();
    canvas.drawPath(area,
        Paint()..color = const Color(0xFF10B981).withOpacity(0.05));

    final line = Path()..moveTo(pts[0].dx, pts[0].dy);
    for (final p in pts.skip(1)) line.lineTo(p.dx, p.dy);
    canvas.drawPath(
        line,
        Paint()
          ..color = const Color(0xFF10B981)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.5
          ..strokeCap = StrokeCap.round
          ..strokeJoin = StrokeJoin.round);

    final last = pts.last;
    canvas.drawCircle(
        last, 6, Paint()..color = const Color(0xFF10B981).withOpacity(0.15));
    canvas.drawCircle(last, 2.5, Paint()..color = const Color(0xFF10B981));
  }

  @override
  bool shouldRepaint(_ChartPainter old) => old.totalSaved != totalSaved;
}

// ── SaveUp mark ───────────────────────────────────────────────────────────

class SaveUpMark extends StatelessWidget {
  final double size;
  const SaveUpMark({super.key, this.size = 32});

  @override
  Widget build(BuildContext context) =>
      SizedBox(width: size, height: size, child: CustomPaint(painter: _Mark()));
}

class _Mark extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final em = const Color(0xFF10B981);
    final cx = w / 2;
    final cy = h / 2;
    final r = w * 0.44;

    final hexPath = Path();
    for (int i = 0; i < 6; i++) {
      final a = math.pi / 6 + i * math.pi / 3;
      final p = Offset(cx + r * math.cos(a), cy + r * math.sin(a));
      i == 0 ? hexPath.moveTo(p.dx, p.dy) : hexPath.lineTo(p.dx, p.dy);
    }
    hexPath.close();
    canvas.drawPath(hexPath, Paint()..color = em.withOpacity(0.07));
    canvas.drawPath(
        hexPath,
        Paint()
          ..color = em
          ..style = PaintingStyle.stroke
          ..strokeWidth = w * 0.044
          ..strokeJoin = StrokeJoin.round);

    final curve = Path()
      ..moveTo(w * 0.328, h * 0.5)
      ..cubicTo(w * 0.328, h * 0.5, w * 0.453, h * 0.609, w * 0.5, h * 0.609)
      ..cubicTo(w * 0.547, h * 0.609, w * 0.672, h * 0.5, w * 0.672, h * 0.5);
    canvas.drawPath(
        curve,
        Paint()
          ..color = em
          ..style = PaintingStyle.stroke
          ..strokeWidth = w * 0.044
          ..strokeCap = StrokeCap.round);

    canvas.drawLine(
        Offset(cx, h * 0.344),
        Offset(cx, h * 0.609),
        Paint()
          ..color = em.withOpacity(0.45)
          ..style = PaintingStyle.stroke
          ..strokeWidth = w * 0.031
          ..strokeCap = StrokeCap.round);
  }

  @override
  bool shouldRepaint(_) => false;
}

// ── Error / Empty state ───────────────────────────────────────────────────

class ErrorRetry extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const ErrorRetry({super.key, required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.wifi_off_outlined, size: 36, color: AppColors.white20),
            const SizedBox(height: 12),
            Text(message,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.white30, fontSize: 13)),
            const SizedBox(height: 20),
            GestureDetector(
              onTap: onRetry,
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.white05,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.white07),
                ),
                child: const Text('Retry',
                    style: TextStyle(
                        color: AppColors.white50, fontWeight: FontWeight.w500)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
