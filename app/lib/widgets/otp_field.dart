import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../core/theme/app_theme.dart';

class OtpField extends StatefulWidget {
  final int length;
  final ValueChanged<String> onCompleted;
  final VoidCallback? onChanged;

  const OtpField({
    super.key,
    this.length = 6,
    required this.onCompleted,
    this.onChanged,
  });

  @override
  State<OtpField> createState() => _OtpFieldState();
}

class _OtpFieldState extends State<OtpField> {
  late final List<TextEditingController> _controllers;
  late final List<FocusNode> _nodes;

  @override
  void initState() {
    super.initState();
    _controllers = List.generate(widget.length, (_) => TextEditingController());
    _nodes = List.generate(widget.length, (_) => FocusNode());
  }

  @override
  void dispose() {
    for (final c in _controllers) c.dispose();
    for (final n in _nodes) n.dispose();
    super.dispose();
  }

  String get _otp => _controllers.map((c) => c.text).join();

  void _onChanged(int i, String val) {
    if (val.length > 1) {
      final digits = val.replaceAll(RegExp(r'\D'), '');
      for (int k = 0; k < widget.length && k < digits.length; k++) {
        _controllers[k].text = digits[k];
      }
      setState(() {});
      if (_otp.length == widget.length) widget.onCompleted(_otp);
      FocusScope.of(context)
          .requestFocus(_nodes[(digits.length - 1).clamp(0, widget.length - 1)]);
      return;
    }
    setState(() {});
    if (val.isNotEmpty && i < widget.length - 1) {
      FocusScope.of(context).requestFocus(_nodes[i + 1]);
    }
    widget.onChanged?.call();
    if (_otp.length == widget.length && !_otp.contains('')) {
      widget.onCompleted(_otp);
    }
  }

  void _onKey(int i, KeyEvent e) {
    if (e is KeyDownEvent &&
        e.logicalKey == LogicalKeyboardKey.backspace &&
        _controllers[i].text.isEmpty &&
        i > 0) {
      FocusScope.of(context).requestFocus(_nodes[i - 1]);
      _controllers[i - 1].clear();
      setState(() {});
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(widget.length, (i) {
        final filled = _controllers[i].text.isNotEmpty;
        return Padding(
          padding: EdgeInsets.only(right: i < widget.length - 1 ? 10 : 0),
          child: KeyboardListener(
            focusNode: FocusNode(),
            onKeyEvent: (e) => _onKey(i, e),
            child: SizedBox(
              width: 48,
              height: 56,
              child: TextField(
                controller: _controllers[i],
                focusNode: _nodes[i],
                onChanged: (v) => _onChanged(i, v),
                textAlign: TextAlign.center,
                keyboardType: TextInputType.number,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(1),
                ],
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w500,
                ),
                decoration: InputDecoration(
                  filled: true,
                  fillColor:
                      filled ? const Color(0x0F10B981) : AppColors.white04,
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(
                      color: filled
                          ? const Color(0x5910B981)
                          : AppColors.white07,
                    ),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide:
                        const BorderSide(color: Color(0x7310B981)),
                  ),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
            ),
          ),
        );
      }),
    );
  }
}
