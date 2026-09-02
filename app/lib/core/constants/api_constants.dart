class ApiConstants {
  // Change to your server host for production.
  // For local dev: Android emulator → 10.0.2.2, iOS sim → localhost.
  static const baseUrl = 'http://10.0.2.2:8000';
  static const prefix = '/api/v1';

  // Auth
  static const sendOtp = '$prefix/auth/send-otp';
  static const verifyOtp = '$prefix/auth/verify-otp';
  static const refresh = '$prefix/auth/refresh';
  static const logout = '$prefix/auth/logout';

  // User
  static const me = '$prefix/users/me';

  // Dashboard
  static const dashboard = '$prefix/dashboard';

  // Goals
  static const goals = '$prefix/goals';
  static String goal(String id) => '$prefix/goals/$id';
  static String goalWithdraw(String id) => '$prefix/goals/$id/withdraw';

  // Payments
  static const createOrder = '$prefix/payments/create-order';
  static const verifyPayment = '$prefix/payments/verify';

  // Transactions
  static const transactions = '$prefix/transactions';

  // Withdrawals
  static const withdrawals = '$prefix/withdrawals';
  static String withdrawal(String id) => '$prefix/withdrawals/$id';
  static String withdrawalResendOtp(String id) =>
      '$prefix/withdrawals/$id/resend-otp';
  static String withdrawalCancel(String id) =>
      '$prefix/withdrawals/$id/cancel';
  static String withdrawalComplete(String id) =>
      '$prefix/withdrawals/$id/complete';

  // Emergency contacts
  static const emergencyContacts = '$prefix/emergency-contacts';
  static String emergencyContact(String id) =>
      '$prefix/emergency-contacts/$id';
}
