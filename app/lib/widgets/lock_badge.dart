import 'package:flutter/material.dart';
import '../models/goal.dart';
import '../core/theme/app_theme.dart';

class LockBadge extends StatelessWidget {
  final LockType lock;

  const LockBadge({super.key, required this.lock});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color border;
    Color fg;

    switch (lock) {
      case LockType.hardLock:
        bg = Colors.transparent;
        border = AppColors.white15;
        fg = AppColors.white40;
        break;
      case LockType.mediumLock:
        bg = const Color(0x14FBBF24);
        border = const Color(0x4DFBBF24);
        fg = const Color(0xCCFBBF24);
        break;
      case LockType.easyLock:
        bg = const Color(0x1210B981);
        border = const Color(0x4010B981);
        fg = const Color(0xCC34D399);
        break;
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
          Text(
            lock.label,
            style: TextStyle(
              color: fg,
              fontSize: 9,
              fontWeight: FontWeight.w500,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}
