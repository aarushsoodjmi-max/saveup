import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AppColors {
  static const bg = Color(0xFF0F1115);
  static const surface = Color(0x09FFFFFF);
  static const surfaceBorder = Color(0x12FFFFFF);
  static const emerald = Color(0xFF10B981);
  static const emeraldLight = Color(0xFF34D399);
  static const white80 = Color(0xCCFFFFFF);
  static const white60 = Color(0x99FFFFFF);
  static const white50 = Color(0x80FFFFFF);
  static const white40 = Color(0x66FFFFFF);
  static const white30 = Color(0x4DFFFFFF);
  static const white25 = Color(0x40FFFFFF);
  static const white20 = Color(0x33FFFFFF);
  static const white15 = Color(0x26FFFFFF);
  static const white10 = Color(0x1AFFFFFF);
  static const white07 = Color(0x12FFFFFF);
  static const white05 = Color(0x0DFFFFFF);
  static const white04 = Color(0x0AFFFFFF);
  static const white03 = Color(0x08FFFFFF);
  static const amber = Color(0xFFFBBF24);
  static const red = Color(0xFFEF4444);
}

class AppTheme {
  static ThemeData get dark => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: AppColors.bg,
        colorScheme: const ColorScheme.dark(
          primary: AppColors.emerald,
          surface: AppColors.bg,
          onSurface: Colors.white,
        ),
        fontFamily: 'SF Pro Display',
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            TargetPlatform.android: CupertinoPageTransitionsBuilder(),
            TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          },
        ),
      );

  static SystemUiOverlayStyle get overlayStyle => const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
        systemNavigationBarColor: Color(0xFF0C0E11),
        systemNavigationBarIconBrightness: Brightness.light,
      );
}
