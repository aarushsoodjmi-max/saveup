import 'package:flutter/material.dart';
import 'dart:math' as math;

class SaveUpMark extends StatelessWidget {
  final double size;

  const SaveUpMark({super.key, this.size = 32});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _MarkPainter()),
    );
  }
}

class _MarkPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final emerald = const Color(0xFF10B981);

    final hexPaint = Paint()
      ..color = emerald.withOpacity(0.07)
      ..style = PaintingStyle.fill;
    final hexStroke = Paint()
      ..color = emerald
      ..style = PaintingStyle.stroke
      ..strokeWidth = w * 0.044
      ..strokeJoin = StrokeJoin.round;

    final cx = w / 2;
    final cy = h / 2;
    final r = w * 0.44;

    final hexPath = Path();
    for (int i = 0; i < 6; i++) {
      final angle = math.pi / 6 + i * math.pi / 3;
      final px = cx + r * math.cos(angle);
      final py = cy + r * math.sin(angle);
      if (i == 0) {
        hexPath.moveTo(px, py);
      } else {
        hexPath.lineTo(px, py);
      }
    }
    hexPath.close();
    canvas.drawPath(hexPath, hexPaint);
    canvas.drawPath(hexPath, hexStroke);

    final curvePaint = Paint()
      ..color = emerald
      ..style = PaintingStyle.stroke
      ..strokeWidth = w * 0.044
      ..strokeCap = StrokeCap.round;

    final curvePath = Path();
    curvePath.moveTo(w * 0.328, h * 0.5);
    curvePath.cubicTo(
      w * 0.328, h * 0.5,
      w * 0.453, h * 0.609,
      w * 0.5, h * 0.609,
    );
    curvePath.cubicTo(
      w * 0.547, h * 0.609,
      w * 0.672, h * 0.5,
      w * 0.672, h * 0.5,
    );
    canvas.drawPath(curvePath, curvePaint);

    final linePaint = Paint()
      ..color = emerald.withOpacity(0.45)
      ..style = PaintingStyle.stroke
      ..strokeWidth = w * 0.031
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(
      Offset(cx, h * 0.344),
      Offset(cx, h * 0.609),
      linePaint,
    );
  }

  @override
  bool shouldRepaint(_) => false;
}
