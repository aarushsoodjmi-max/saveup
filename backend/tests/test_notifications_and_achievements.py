"""Notifications feed and achievement auto-unlock on deposit."""

from decimal import Decimal

from app.models.achievement import Achievement
from app.models.goal import Goal
from app.services.ledger_service import LedgerService


def test_deposit_triggers_deposit_notification(client, make_user, auth_headers, db_session):
    user = make_user()
    goal = Goal(
        user_id=user.id,
        title="Notif Goal",
        category="General",
        target_amount=Decimal("500.00"),
        lock_type="EASY",
        status="ACTIVE",
    )
    db_session.add(goal)
    db_session.commit()

    LedgerService(db_session).deposit(user=user, goal_id=goal.id, amount=Decimal("50.00"))
    from app.services.notification_service import NotificationService

    NotificationService(db_session).notify_deposit(user_id=user.id, goal_title=goal.title, amount=Decimal("50.00"))

    response = client.get("/api/v1/notifications", headers=auth_headers(user))
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] >= 1
    assert any(n["type"] == "PAYMENT" for n in body["items"])


def test_mark_notification_read(client, make_user, auth_headers, db_session):
    from app.services.notification_service import NotificationService

    user = make_user()
    notification = NotificationService(db_session).notify(
        user_id=user.id, title="Test", message="Hello", type_="SYSTEM"
    )

    response = client.patch(f"/api/v1/notifications/{notification.id}/read", headers=auth_headers(user))
    assert response.status_code == 200
    assert response.json()["is_read"] is True


def test_achievement_unlocks_when_metric_threshold_reached(db_session, make_user):
    from app.services.achievement_service import AchievementService

    user = make_user()
    achievement = Achievement(
        code="FIRST_HUNDRED",
        title="First ₹100 Saved",
        metric="TOTAL_SAVED",
        required_value=Decimal("100.00"),
    )
    db_session.add(achievement)
    db_session.commit()

    goal = Goal(
        user_id=user.id,
        title="Achievement Goal",
        category="General",
        target_amount=Decimal("1000.00"),
        lock_type="EASY",
        status="ACTIVE",
    )
    db_session.add(goal)
    db_session.commit()

    LedgerService(db_session).deposit(user=user, goal_id=goal.id, amount=Decimal("150.00"))

    unlocked = AchievementService(db_session).evaluate_and_unlock_for_user(user.id)
    assert any(a.code == "FIRST_HUNDRED" for a in unlocked)

    # Re-evaluating shouldn't unlock it a second time.
    unlocked_again = AchievementService(db_session).evaluate_and_unlock_for_user(user.id)
    assert unlocked_again == []


def test_streak_increments_on_consecutive_days(db_session, make_user):
    from app.services.streak_service import StreakService

    user = make_user()
    service = StreakService(db_session)

    first = service.record_deposit(user.id)
    assert first.current_streak == 1

    # Same day again -- should not double-count.
    second = service.record_deposit(user.id)
    assert second.current_streak == 1
