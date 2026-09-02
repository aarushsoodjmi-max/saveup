enum LockType { hardLock, mediumLock, easyLock }

extension LockTypeExt on LockType {
  String get label {
    switch (this) {
      case LockType.hardLock:
        return 'Hard Lock';
      case LockType.mediumLock:
        return 'Medium Lock';
      case LockType.easyLock:
        return 'Easy Lock';
    }
  }

  String get description {
    switch (this) {
      case LockType.hardLock:
        return 'Cannot withdraw until the goal target is fully met.';
      case LockType.mediumLock:
        return 'Withdraw with a 48-hour mandatory cooling period.';
      case LockType.easyLock:
        return 'Withdraw anytime. No restrictions or penalties.';
    }
  }
}

class Goal {
  final int id;
  final String name;
  final int target;
  final int saved;
  final int daysLeft;
  final LockType lock;
  final String category;
  final String imageUrl;

  const Goal({
    required this.id,
    required this.name,
    required this.target,
    required this.saved,
    required this.daysLeft,
    required this.lock,
    required this.category,
    required this.imageUrl,
  });

  int get remaining => target - saved;
  int get percent => target == 0 ? 0 : ((saved / target) * 100).round();
  int get dailyNeed => daysLeft == 0 ? 0 : (remaining / daysLeft).round();
}

final List<Goal> sampleGoals = [
  const Goal(
    id: 1,
    name: 'iPhone 16 Pro',
    target: 120000,
    saved: 64500,
    daysLeft: 241,
    lock: LockType.hardLock,
    category: 'Gadgets',
    imageUrl:
        'https://images.unsplash.com/photo-1511140973288-19bf21d7e771?w=600&h=360&fit=crop&auto=format',
  ),
  const Goal(
    id: 2,
    name: 'Goa Trip',
    target: 25000,
    saved: 12450,
    daysLeft: 68,
    lock: LockType.mediumLock,
    category: 'Travel',
    imageUrl:
        'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=600&h=360&fit=crop&auto=format',
  ),
  const Goal(
    id: 3,
    name: 'Royal Enfield Classic 350',
    target: 180000,
    saved: 45000,
    daysLeft: 357,
    lock: LockType.hardLock,
    category: 'Vehicle',
    imageUrl:
        'https://images.unsplash.com/photo-1530248809527-ee069dc8373a?w=600&h=360&fit=crop&auto=format',
  ),
  const Goal(
    id: 4,
    name: 'Canon Camera Setup',
    target: 40000,
    saved: 8200,
    daysLeft: 111,
    lock: LockType.easyLock,
    category: 'Gadgets',
    imageUrl:
        'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=600&h=360&fit=crop&auto=format',
  ),
];
