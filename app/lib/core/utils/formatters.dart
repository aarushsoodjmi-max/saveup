import 'package:intl/intl.dart';

class Fmt {
  static final _inr = NumberFormat('#,##,##0', 'en_IN');

  static String currency(num amount) => '₹${_inr.format(amount.round())}';

  static String percent(num saved, num target) =>
      target == 0 ? '0' : ((saved / target) * 100).toStringAsFixed(0);
}
