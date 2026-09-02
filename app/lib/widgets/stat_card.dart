import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import 'glass_card.dart';

class StatCard extends StatelessWidget {
  final String label;
  final String value;
  final String? subtitle;
  final Widget? subtitleWidget;
  final Widget? trailing;

  const StatCard({
    super.key,
    required this.label,
    required this.value,
    this.subtitle,
    this.subtitleWidget,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label.toUpperCase(),
                  style: const TextStyle(
                    color: AppColors.white30,
                    fontSize: 10,
                    letterSpacing: 1.8,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  value,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 28,
                    fontFamily: 'JetBrains Mono',
                    fontWeight: FontWeight.w600,
                    height: 1,
                  ),
                ),
                if (subtitleWidget != null) ...[
                  const SizedBox(height: 8),
                  subtitleWidget!,
                ] else if (subtitle != null) ...[
                  const SizedBox(height: 6),
                  Text(
                    subtitle!,
                    style: const TextStyle(
                      color: AppColors.white25,
                      fontSize: 10,
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}
