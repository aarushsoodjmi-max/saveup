import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../models/api_models.dart';
import '../../routes/app_router.dart';
import '../../services/providers.dart';
import '../../services/api_client.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/glass_button.dart';
import '../../widgets/shared_widgets.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(userProfileProvider);
    final dashAsync = ref.watch(dashboardProvider);
    final contactsAsync = ref.watch(emergencyContactsProvider);

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            Expanded(
              child: CustomScrollView(
                physics: const BouncingScrollPhysics(),
                slivers: [
                  SliverToBoxAdapter(
                    child: profileAsync.when(
                      data: (u) => _ProfileHeader(
                        user: u,
                        dashboard: dashAsync.valueOrNull,
                      ),
                      loading: () => const _LoadingHeader(),
                      error: (e, _) => _ProfileHeader(user: null, dashboard: null),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: profileAsync.maybeWhen(
                      data: (u) => _KycBanner(status: u.kycStatus),
                      orElse: () => const SizedBox.shrink(),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: contactsAsync.when(
                      data: (contacts) => _EmergencyContacts(
                        contacts: contacts,
                        ref: ref,
                      ),
                      loading: () => const SizedBox.shrink(),
                      error: (_, __) => const SizedBox.shrink(),
                    ),
                  ),
                  const SliverToBoxAdapter(child: _SettingsMenu()),
                  const SliverToBoxAdapter(child: _ReferralCard()),
                  SliverToBoxAdapter(
                    child: _SignOutButton(ref: ref),
                  ),
                  const SliverToBoxAdapter(child: SizedBox(height: 12)),
                ],
              ),
            ),
            const BottomNav(current: NavTab.profile),
          ],
        ),
      ),
    );
  }
}

// ── Header ────────────────────────────────────────────────────────────────

class _ProfileHeader extends StatelessWidget {
  final UserProfile? user;
  final DashboardData? dashboard;
  const _ProfileHeader({required this.user, required this.dashboard});

  @override
  Widget build(BuildContext context) {
    final name = user?.name ?? '—';
    final saved = dashboard?.totalSaved ?? 0;
    final goals = dashboard?.activeGoalsCount ?? 0;
    final streak = dashboard?.bestStreak ?? 0;

    final stats = [
      ('Total Saved', '₹${saved.toStringAsFixed(0)}'),
      ('Goals', '$goals'),
      ('Best Streak', '${streak}d'),
    ];

    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
      child: Column(
        children: [
          Row(
            children: [
              Stack(
                children: [
                  Container(
                    width: 62,
                    height: 62,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                          color: const Color(0x3310B981), width: 1.5),
                    ),
                    child: ClipOval(
                      child: user?.profilePicture != null
                          ? Image.network(
                              user!.profilePicture!,
                              fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) => _avatar(),
                            )
                          : _avatar(),
                    ),
                  ),
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: Container(
                      width: 18,
                      height: 18,
                      decoration: const BoxDecoration(
                        color: AppColors.bg,
                        shape: BoxShape.circle,
                      ),
                      child: Container(
                        margin: const EdgeInsets.all(2),
                        decoration: BoxDecoration(
                          color: const Color(0x2610B981),
                          shape: BoxShape.circle,
                          border: Border.all(color: const Color(0x4D10B981)),
                        ),
                        child: const Icon(Icons.check,
                            size: 8, color: AppColors.emeraldLight),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontFamily: 'Georgia',
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0x1410B981),
                        borderRadius: BorderRadius.circular(100),
                        border: Border.all(color: const Color(0x2D10B981)),
                      ),
                      child: const Text(
                        'Premium Member',
                        style: TextStyle(
                          color: Color(0xD934D399),
                          fontSize: 9.5,
                          fontWeight: FontWeight.w500,
                          letterSpacing: 0.4,
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      user?.phoneNumber ?? '',
                      style: const TextStyle(
                        color: AppColors.white20,
                        fontSize: 10.5,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: stats.asMap().entries.map((e) {
              final (label, value) = e.value;
              final isLast = e.key == stats.length - 1;
              return Expanded(
                child: Container(
                  margin: EdgeInsets.only(right: isLast ? 0 : 10),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.surfaceBorder),
                  ),
                  child: Column(
                    children: [
                      Text(
                        value,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13.5,
                          fontWeight: FontWeight.w600,
                          height: 1,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        label,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: AppColors.white25,
                          fontSize: 9.5,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _avatar() => const Icon(Icons.person, color: AppColors.white40, size: 30);
}

class _LoadingHeader extends StatelessWidget {
  const _LoadingHeader();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(40),
      child: Center(
        child: SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(
            strokeWidth: 1.5,
            color: AppColors.emerald,
          ),
        ),
      ),
    );
  }
}

// ── KYC banner ────────────────────────────────────────────────────────────

class _KycBanner extends StatelessWidget {
  final String status;
  const _KycBanner({required this.status});

  @override
  Widget build(BuildContext context) {
    final isVerified = status == 'VERIFIED';
    final color = isVerified
        ? const Color(0xFF10B981)
        : const Color(0xFFFBBF24);
    final label = isVerified ? 'KYC Verified' : 'KYC Pending';
    final sub = isVerified
        ? 'Full access enabled · PAN & Aadhaar linked'
        : 'Complete verification to unlock full access';

    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withOpacity(0.07),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: color.withOpacity(0.22)),
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                isVerified ? Icons.shield_outlined : Icons.shield_outlined,
                size: 15,
                color: color.withOpacity(0.75),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.75),
                      fontSize: 12.5,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(sub,
                      style: TextStyle(
                          color: color.withOpacity(0.45), fontSize: 10.5)),
                ],
              ),
            ),
            Icon(
              isVerified ? Icons.check : Icons.chevron_right,
              size: 14,
              color: color.withOpacity(0.55),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Emergency contacts ────────────────────────────────────────────────────

class _EmergencyContacts extends ConsumerStatefulWidget {
  final List<EmergencyContact> contacts;
  final WidgetRef ref;
  const _EmergencyContacts({required this.contacts, required this.ref});

  @override
  ConsumerState<_EmergencyContacts> createState() => _EmergencyContactsState();
}

class _EmergencyContactsState extends ConsumerState<_EmergencyContacts> {
  bool _adding = false;
  final _nameCtrl = TextEditingController();
  final _relCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _relCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  Future<void> _add() async {
    if (_nameCtrl.text.isEmpty || _phoneCtrl.text.isEmpty) return;
    setState(() => _saving = true);
    try {
      await ref.read(contactRepoProvider).create(
        contactName: _nameCtrl.text.trim(),
        relationshipLabel: _relCtrl.text.trim().isNotEmpty
            ? _relCtrl.text.trim()
            : 'Contact',
        phoneNumber: '+91${_phoneCtrl.text.trim()}',
      );
      ref.invalidate(emergencyContactsProvider);
      setState(() => _adding = false);
      _nameCtrl.clear();
      _relCtrl.clear();
      _phoneCtrl.clear();
    } on ApiException catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.message),
          backgroundColor: const Color(0xFF1A1E25),
        ),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _delete(String id) async {
    try {
      await ref.read(contactRepoProvider).delete(id);
      ref.invalidate(emergencyContactsProvider);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'EMERGENCY CONTACTS',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.22),
                  fontSize: 9.5,
                  letterSpacing: 2.2,
                  fontWeight: FontWeight.w500,
                ),
              ),
              GestureDetector(
                onTap: () => setState(() => _adding = !_adding),
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0x1210B981),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0x2610B981)),
                  ),
                  child: Text(
                    _adding ? 'Cancel' : '+ Add',
                    style: const TextStyle(
                      color: Color(0xCC34D399),
                      fontSize: 10,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (widget.contacts.isEmpty && !_adding)
            Text(
              'No emergency contacts yet.',
              style: TextStyle(
                color: Colors.white.withOpacity(0.25),
                fontSize: 12,
              ),
            ),
          ...widget.contacts.map((c) => Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.white03,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.white07),
            ),
            child: Row(children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: AppColors.white05,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.white07),
                ),
                child: const Icon(Icons.person_outline,
                    size: 14, color: AppColors.white40),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(c.contactName,
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.75),
                            fontSize: 13,
                            fontWeight: FontWeight.w500)),
                    Text(
                      '${c.relationshipLabel} · ${c.phoneNumber}',
                      style: const TextStyle(
                          color: AppColors.white25, fontSize: 10),
                    ),
                  ],
                ),
              ),
              GestureDetector(
                onTap: () => _delete(c.id),
                child: const Icon(Icons.delete_outline,
                    size: 15, color: AppColors.white20),
              ),
            ]),
          )),
          if (_adding) ...[
            const SizedBox(height: 8),
            GlassCard(
              backgroundColor: AppColors.white03,
              borderColor: AppColors.white07,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _Field('Name', _nameCtrl, 'e.g. Priya Sharma'),
                  const SizedBox(height: 10),
                  _Field('Relationship', _relCtrl, 'e.g. Sister'),
                  const SizedBox(height: 10),
                  _Field('Phone', _phoneCtrl, '98765 43210',
                      type: TextInputType.phone),
                  const SizedBox(height: 14),
                  GlassButton(
                    label: 'Save Contact',
                    loading: _saving,
                    onTap: _add,
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Field extends StatelessWidget {
  final String label;
  final TextEditingController ctrl;
  final String hint;
  final TextInputType type;
  const _Field(this.label, this.ctrl, this.hint,
      {this.type = TextInputType.text});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: TextStyle(
                color: Colors.white.withOpacity(0.30),
                fontSize: 10,
                letterSpacing: 1.5)),
        const SizedBox(height: 6),
        TextField(
          controller: ctrl,
          keyboardType: type,
          style: const TextStyle(color: Colors.white, fontSize: 13),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle:
                TextStyle(color: Colors.white.withOpacity(0.15), fontSize: 13),
            filled: true,
            fillColor: AppColors.white04,
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AppColors.white07),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: Color(0x3310B981)),
            ),
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            isDense: true,
          ),
        ),
      ],
    );
  }
}

// ── Settings menu ─────────────────────────────────────────────────────────

class _SettingsMenu extends StatelessWidget {
  const _SettingsMenu();

  static const _items = [
    (Icons.notifications_outlined, 'Notifications',
        'Deposits, streaks, goal reminders'),
    (Icons.shield_outlined, 'Security', 'PIN, biometrics, two-factor auth'),
    (Icons.credit_card_outlined, 'Linked Banks',
        'Manage your bank accounts'),
    (Icons.settings_outlined, 'Preferences', 'Theme, language, currency'),
  ];

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('ACCOUNT',
              style: TextStyle(
                  color: Colors.white.withOpacity(0.22),
                  fontSize: 9.5,
                  letterSpacing: 2.2,
                  fontWeight: FontWeight.w500)),
          const SizedBox(height: 12),
          GlassCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: _items.asMap().entries.map((e) {
                final (icon, label, desc) = e.value;
                final isLast = e.key == _items.length - 1;
                return GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () {},
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 14),
                    decoration: BoxDecoration(
                      border: isLast
                          ? null
                          : const Border(
                              bottom: BorderSide(color: Color(0x0DFFFFFF))),
                    ),
                    child: Row(children: [
                      Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          color: AppColors.white05,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(icon, size: 14, color: AppColors.white40),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(label,
                                style: const TextStyle(
                                    color: AppColors.white80,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500)),
                            Text(desc,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                    color: AppColors.white25, fontSize: 10.5)),
                          ],
                        ),
                      ),
                      const Icon(Icons.chevron_right,
                          size: 15, color: Color(0x2EFFFFFF)),
                    ]),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Referral ──────────────────────────────────────────────────────────────

class _ReferralCard extends StatelessWidget {
  const _ReferralCard();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
      child: GlassCard(
        backgroundColor: AppColors.white03,
        borderColor: AppColors.white07,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Refer & Earn',
                style: TextStyle(
                    color: Colors.white.withOpacity(0.55),
                    fontSize: 12.5,
                    fontWeight: FontWeight.w500)),
            const SizedBox(height: 4),
            Text(
                'Invite a friend and both get ₹250 bonus on the first deposit.',
                style: TextStyle(
                    color: Colors.white.withOpacity(0.25),
                    fontSize: 11,
                    height: 1.5)),
            const SizedBox(height: 12),
            GestureDetector(
              onTap: () {},
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.white05,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.white07),
                ),
                child: const Text('Share Invite Link',
                    style: TextStyle(
                        color: AppColors.white40,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w500)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Sign out ──────────────────────────────────────────────────────────────

class _SignOutButton extends StatefulWidget {
  final WidgetRef ref;
  const _SignOutButton({required this.ref});

  @override
  State<_SignOutButton> createState() => _SignOutButtonState();
}

class _SignOutButtonState extends State<_SignOutButton> {
  bool _loading = false;

  Future<void> _signOut() async {
    setState(() => _loading = true);
    try {
      await widget.ref.read(authRepoProvider).logout();
    } catch (_) {}
    if (!mounted) return;
    context.go(AppRoutes.splash);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
      child: GlassButton(
        label: 'Sign Out',
        variant: GlassButtonVariant.danger,
        loading: _loading,
        onTap: _signOut,
        leading: const Icon(Icons.logout, size: 15, color: Color(0x99EF4444)),
      ),
    );
  }
}
