import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

enum GlassButtonVariant { emerald, subtle, danger }

class GlassButton extends StatefulWidget {
  final String label;
  final VoidCallback? onTap;
  final GlassButtonVariant variant;
  final bool enabled;
  final bool loading;
  final Widget? leading;

  const GlassButton({
    super.key,
    required this.label,
    this.onTap,
    this.variant = GlassButtonVariant.emerald,
    this.enabled = true,
    this.loading = false,
    this.leading,
  });

  @override
  State<GlassButton> createState() => _GlassButtonState();
}

class _GlassButtonState extends State<GlassButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 100));
  late final Animation<double> _scale =
      Tween(begin: 1.0, end: 0.97).animate(_ctrl);

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  bool get _active => widget.enabled && !widget.loading;

  Color get _bg {
    if (!_active) return AppColors.white03;
    switch (widget.variant) {
      case GlassButtonVariant.emerald:
        return const Color(0x17109B61);
      case GlassButtonVariant.subtle:
        return AppColors.white05;
      case GlassButtonVariant.danger:
        return const Color(0x14EF4444);
    }
  }

  Color get _border {
    if (!_active) return AppColors.white05;
    switch (widget.variant) {
      case GlassButtonVariant.emerald:
        return const Color(0x4010B981);
      case GlassButtonVariant.subtle:
        return AppColors.white10;
      case GlassButtonVariant.danger:
        return const Color(0x30EF4444);
    }
  }

  Color get _fg {
    if (!_active) return AppColors.white15;
    switch (widget.variant) {
      case GlassButtonVariant.emerald:
        return AppColors.emeraldLight;
      case GlassButtonVariant.subtle:
        return AppColors.white50;
      case GlassButtonVariant.danger:
        return const Color(0xDDEF4444);
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: _active ? (_) => _ctrl.forward() : null,
      onTapUp: _active
          ? (_) {
              _ctrl.reverse();
              widget.onTap?.call();
            }
          : null,
      onTapCancel: _active ? () => _ctrl.reverse() : null,
      child: ScaleTransition(
        scale: _scale,
        child: Container(
          height: 52,
          decoration: BoxDecoration(
            color: _bg,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: _border),
          ),
          child: Center(
            child: widget.loading
                ? SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: _fg,
                    ),
                  )
                : Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (widget.leading != null) ...[
                        widget.leading!,
                        const SizedBox(width: 8),
                      ],
                      Text(
                        widget.label.toUpperCase(),
                        style: TextStyle(
                          color: _fg,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 1.8,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}
