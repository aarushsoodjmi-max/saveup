import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

class SavingsChart extends StatelessWidget {
  const SavingsChart({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          height: 78,
          child: CustomPaint(
            painter: _ChartPainter(),
            size: const Size(double.infinity, 78),
          ),
        ),
        const SizedBox(height: 6),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: ['1 May', '8', '15', '22', '29 May']
              .map((l) => Text(
                    l,
                    style: const TextStyle(
                      color: AppColors.white20,
                      fontSize: 9,
                      fontFamily: 'JetBrains Mono',
                    ),
                  ))
              .toList(),
        ),
      ],
    );
  }
}

class _ChartPainter extends CustomPainter {
  final data = const [16000, 24000, 33000, 44000, 54000, 64000, 76000, 87450];
  static const maxVal = 95000.0;

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    List<Offset> pts = [];
    for (int i = 0; i < data.length; i++) {
      final x = (i / (data.length - 1)) * w;
      final y = h - (data[i] / maxVal) * h * 0.92;
      pts.add(Offset(x, y));
    }

    final linePath = Path();
    linePath.moveTo(pts[0].dx, pts[0].dy);
    for (int i = 1; i < pts.length; i++) {
      linePath.lineTo(pts[i].dx, pts[i].dy);
    }

    final areaPath = Path.from(linePath);
    areaPath.lineTo(w, h);
    areaPath.lineTo(0, h);
    areaPath.close();

    canvas.drawPath(
      areaPath,
      Paint()
        ..color = const Color(0xFF10B981).withOpacity(0.05)
        ..style = PaintingStyle.fill,
    );

    canvas.drawPath(
      linePath,
      Paint()
        ..color = const Color(0xFF10B981)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );

    final last = pts.last;

    canvas.drawCircle(
      last,
      6,
      Paint()..color = const Color(0xFF10B981).withOpacity(0.15),
    );
    canvas.drawCircle(
      last,
      2.5,
      Paint()..color = const Color(0xFF10B981),
    );

    final tp = TextPainter(
      text: const TextSpan(
        text: '₹87,450',
        style: TextStyle(
          color: Color(0xFF34D399),
          fontSize: 8.5,
          fontFamily: 'JetBrains Mono',
          fontWeight: FontWeight.w500,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();

    tp.paint(canvas, Offset(last.dx - tp.width / 2, last.dy - 18));
  }

  @override
  bool shouldRepaint(_) => false;
}
