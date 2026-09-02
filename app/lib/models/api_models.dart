// ignore_for_file: non_constant_identifier_names

// ── Auth ──────────────────────────────────────────────────────────────────

class SendOtpResponse {
  final String message;
  final int otpExpiresInSeconds;
  final int resendAvailableInSeconds;
  final String? debugOtp;

  SendOtpResponse.fromJson(Map<String, dynamic> j)
      : message = j['message'],
        otpExpiresInSeconds = j['otp_expires_in_seconds'],
        resendAvailableInSeconds = j['resend_available_in_seconds'],
        debugOtp = j['debug_otp'];
}

class TokenPair {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;

  TokenPair.fromJson(Map<String, dynamic> j)
      : accessToken = j['access_token'],
        refreshToken = j['refresh_token'],
        tokenType = j['token_type'] ?? 'bearer',
        expiresIn = j['expires_in'];
}

class AuthResponse extends TokenPair {
  final bool isNewUser;

  AuthResponse.fromJson(Map<String, dynamic> j)
      : isNewUser = j['is_new_user'] ?? false,
        super.fromJson(j);
}

// ── User ──────────────────────────────────────────────────────────────────

class UserProfile {
  final String id;
  final String phoneNumber;
  final String name;
  final String? email;
  final String? profilePicture;
  final String? dateOfBirth;
  final String kycStatus;
  final String role;
  final bool isActive;
  final String createdAt;

  UserProfile.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        phoneNumber = j['phone_number'],
        name = j['name'],
        email = j['email'],
        profilePicture = j['profile_picture'],
        dateOfBirth = j['date_of_birth'],
        kycStatus = j['kyc_status'],
        role = j['role'],
        isActive = j['is_active'],
        createdAt = j['created_at'];
}

// ── Dashboard ─────────────────────────────────────────────────────────────

class DashboardData {
  final double totalSaved;
  final int activeGoalsCount;
  final int completedGoalsCount;
  final int currentStreak;
  final int bestStreak;
  final int unreadNotifications;
  final int unlockedAchievementsCount;

  DashboardData.fromJson(Map<String, dynamic> j)
      : totalSaved = double.parse(j['total_saved'].toString()),
        activeGoalsCount = j['active_goals_count'],
        completedGoalsCount = j['completed_goals_count'],
        currentStreak = j['current_streak'],
        bestStreak = j['best_streak'],
        unreadNotifications = j['unread_notifications'],
        unlockedAchievementsCount = j['unlocked_achievements_count'];
}

// ── Goal ──────────────────────────────────────────────────────────────────

class GoalModel {
  final String id;
  final String userId;
  final String title;
  final String? description;
  final String category;
  final String? goalImage;
  final double targetAmount;
  final double savedAmount;
  final double? monthlyTarget;
  final String? deadline;
  final String lockType;
  final String status;
  final String? completedAt;
  final String createdAt;
  final String updatedAt;
  final double remainingAmount;
  final double progressPercentage;

  GoalModel.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        userId = j['user_id'],
        title = j['title'],
        description = j['description'],
        category = j['category'],
        goalImage = j['goal_image'],
        targetAmount = double.parse(j['target_amount'].toString()),
        savedAmount = double.parse(j['saved_amount'].toString()),
        monthlyTarget = j['monthly_target'] != null
            ? double.parse(j['monthly_target'].toString())
            : null,
        deadline = j['deadline'],
        lockType = j['lock_type'],
        status = j['status'],
        completedAt = j['completed_at'],
        createdAt = j['created_at'],
        updatedAt = j['updated_at'],
        remainingAmount = double.parse(j['remaining_amount'].toString()),
        progressPercentage = (j['progress_percentage'] as num).toDouble();

  int get daysLeft {
    if (deadline == null) return 0;
    try {
      final d = DateTime.parse(deadline!);
      return d.difference(DateTime.now()).inDays.clamp(0, 9999);
    } catch (_) {
      return 0;
    }
  }

  int get dailyNeed {
    final dl = daysLeft;
    if (dl == 0) return 0;
    return (remainingAmount / dl).round();
  }

  String get imageUrlOrFallback {
    if (goalImage != null && goalImage!.startsWith('http')) return goalImage!;
    switch (category.toLowerCase()) {
      case 'travel':
        return 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=600&h=360&fit=crop';
      case 'gadgets':
        return 'https://images.unsplash.com/photo-1511140973288-19bf21d7e771?w=600&h=360&fit=crop';
      case 'vehicle':
        return 'https://images.unsplash.com/photo-1530248809527-ee069dc8373a?w=600&h=360&fit=crop';
      default:
        return 'https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=600&h=360&fit=crop';
    }
  }
}

// ── Transaction ───────────────────────────────────────────────────────────

class TxnModel {
  final String id;
  final String goalId;
  final String transactionType;
  final double amount;
  final String status;
  final double? balanceAfter;
  final String? referenceType;
  final String createdAt;

  TxnModel.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        goalId = j['goal_id'],
        transactionType = j['transaction_type'],
        amount = double.parse(j['amount'].toString()),
        status = j['status'],
        balanceAfter = j['balance_after'] != null
            ? double.parse(j['balance_after'].toString())
            : null,
        referenceType = j['reference_type'],
        createdAt = j['created_at'];

  String get formattedDate {
    try {
      final dt = DateTime.parse(createdAt).toLocal();
      const months = [
        '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
      ];
      return '${dt.day} ${months[dt.month]}, ${dt.year}';
    } catch (_) {
      return createdAt;
    }
  }
}

// ── Payment ───────────────────────────────────────────────────────────────

class PaymentOrder {
  final String id;
  final String goalId;
  final double amount;
  final String currency;
  final String provider;
  final String providerOrderId;
  final String status;

  PaymentOrder.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        goalId = j['goal_id'],
        amount = double.parse(j['amount'].toString()),
        currency = j['currency'],
        provider = j['provider'],
        providerOrderId = j['provider_order_id'],
        status = j['status'];
}

// ── Emergency Contact ─────────────────────────────────────────────────────

class EmergencyContact {
  final String id;
  final String contactName;
  final String relationshipLabel;
  final String phoneNumber;
  final bool isVerified;
  final String createdAt;

  EmergencyContact.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        contactName = j['contact_name'],
        relationshipLabel = j['relationship_label'],
        phoneNumber = j['phone_number'],
        isVerified = j['is_verified'] ?? false,
        createdAt = j['created_at'];
}

// ── Withdrawal ────────────────────────────────────────────────────────────

class WithdrawalModel {
  final String id;
  final String goalId;
  final double amount;
  final String reason;
  final String? reasonNotes;
  final String status;
  final String? cooldownEndsAt;
  final String? rejectionReason;
  final String requestedAt;
  final String? debugOtp;

  WithdrawalModel.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        goalId = j['goal_id'],
        amount = double.parse(j['amount'].toString()),
        reason = j['reason'],
        reasonNotes = j['reason_notes'],
        status = j['status'],
        cooldownEndsAt = j['cooldown_ends_at'],
        rejectionReason = j['rejection_reason'],
        requestedAt = j['requested_at'],
        debugOtp = j['debug_otp'];
}

// ── Paginated wrapper ─────────────────────────────────────────────────────

class Paginated<T> {
  final List<T> items;
  final int total;
  final int page;
  final int limit;

  Paginated({
    required this.items,
    required this.total,
    required this.page,
    required this.limit,
  });

  factory Paginated.fromJson(
    Map<String, dynamic> j,
    T Function(Map<String, dynamic>) fromJson,
  ) {
    final meta = j['meta'] as Map<String, dynamic>;
    return Paginated(
      items: (j['items'] as List).map((e) => fromJson(e)).toList(),
      total: meta['total'],
      page: meta['page'],
      limit: meta['limit'],
    );
  }
}
