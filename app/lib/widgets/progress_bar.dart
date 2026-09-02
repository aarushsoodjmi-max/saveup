import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

class AppProgressBar extends StatelessWidget {
  final int value;
  final double height;

  const AppProgressBar({super.key, required this.value, this.height = 3});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(100),
      child: LinearProgressIndicator(
        value: (value.clamp(0, 100)) / 100,
        backgroundColor: AppColors.white07,
        valueColor: const AlwaysStoppedAnimation(AppColors.emerald),
        minHeight: height,
      ),
    );
  }
}
