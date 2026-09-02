import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../core/theme/app_theme.dart';

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
              child: const Icon(
                Icons.chevron_left,
                color: AppColors.white50,
                size: 20,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Text(
            title,
            style: const TextStyle(
              color: AppColors.white80,
              fontSize: 14,
              fontWeight: FontWeight.w500,
              letterSpacing: 0.4,
            ),
          ),
        ],
      ),
    );
  }
}
