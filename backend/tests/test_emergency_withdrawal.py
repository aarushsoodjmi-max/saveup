"""Emergency withdrawal state machine for MEDIUM/HARD lock goals."""

from datetime import timedelta
from decimal import Decimal

from app.core.time_utils import utc_now
from app.models.goal import Goal
from app.services.ledger_service import LedgerService


def _make_funded_goal(db_session, user, *, lock_type="MEDIUM", saved="500.00"):
    goal = Goal(
        user_id=user.id,
        title="Emergency Fund",
        category="Safety",
        target_amount=Decimal("1000.00"),
        lock_type=lock_type,
        status="ACTIVE",
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    LedgerService(db_session).deposit(user=user, goal_id=goal.id, amount=Decimal(saved))
    db_session.refresh(goal)
    return goal


def _add_contact(client, headers):
    response = client.post(
        "/api/v1/emergency-contacts",
        json={"contact_name": "Mom", "relationship_label": "Parent", "phone_number": "+15551230000"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_easy_lock_goal_cannot_use_emergency_workflow(client, make_user, auth_headers, db_session):
    user = make_user()
    goal = _make_funded_goal(db_session, user, lock_type="EASY")
    contact_id = _add_contact(client, auth_headers(user))

    response = client.post(
        "/api/v1/withdrawals",
        json={
            "goal_id": str(goal.id),
            "emergency_contact_id": contact_id,
            "amount": "50.00",
            "reason": "OTHER",
        },
        headers=auth_headers(user),
    )
    assert response.status_code == 409


def test_full_medium_lock_withdrawal_flow(client, make_user, auth_headers, db_session, monkeypatch):
    from app.core import enums as enums_module

    # Shrink the cooldown so the test doesn't need to sleep for real hours
    # (0.1s instead of 24h) -- comfortably covered by the sleep below.
    monkeypatch.setitem(enums_module.LOCK_TYPE_COOLDOWN_HOURS, "MEDIUM", 1 / 36000)

    user = make_user()
    goal = _make_funded_goal(db_session, user, lock_type="MEDIUM", saved="200.00")
    contact_id = _add_contact(client, auth_headers(user))
    headers = auth_headers(user)

    create_response = client.post(
        "/api/v1/withdrawals",
        json={
            "goal_id": str(goal.id),
            "emergency_contact_id": contact_id,
            "amount": "100.00",
            "reason": "MEDICAL",
            "reason_notes": "Urgent care visit",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["status"] == "PENDING"
    otp = body["debug_otp"]
    request_id = body["id"]

    # Approving is contact-facing and deliberately unauthenticated.
    approve_response = client.post(f"/api/v1/withdrawals/{request_id}/approve", json={"otp": otp})
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "COOLDOWN"

    import time

    time.sleep(1)  # comfortably past the ~0.1s patched cooldown

    complete_response = client.post(f"/api/v1/withdrawals/{request_id}/complete", headers=headers)
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "COMPLETED"

    db_session.refresh(goal)
    assert goal.saved_amount == Decimal("100.00")  # 200 - 100


def test_withdrawal_wrong_otp_is_rejected(client, make_user, auth_headers, db_session):
    user = make_user()
    goal = _make_funded_goal(db_session, user, lock_type="HARD", saved="300.00")
    contact_id = _add_contact(client, auth_headers(user))

    create_response = client.post(
        "/api/v1/withdrawals",
        json={
            "goal_id": str(goal.id),
            "emergency_contact_id": contact_id,
            "amount": "100.00",
            "reason": "FAMILY",
        },
        headers=auth_headers(user),
    )
    request_id = create_response.json()["id"]

    response = client.post(f"/api/v1/withdrawals/{request_id}/approve", json={"otp": "000000"})
    assert response.status_code == 400


def test_completing_before_cooldown_ends_is_rejected(client, make_user, auth_headers, db_session):
    user = make_user()
    goal = _make_funded_goal(db_session, user, lock_type="HARD", saved="300.00")
    contact_id = _add_contact(client, auth_headers(user))
    headers = auth_headers(user)

    create_response = client.post(
        "/api/v1/withdrawals",
        json={
            "goal_id": str(goal.id),
            "emergency_contact_id": contact_id,
            "amount": "100.00",
            "reason": "FAMILY",
        },
        headers=headers,
    )
    body = create_response.json()
    otp, request_id = body["debug_otp"], body["id"]

    approve_response = client.post(f"/api/v1/withdrawals/{request_id}/approve", json={"otp": otp})
    assert approve_response.json()["status"] == "COOLDOWN"  # HARD lock -> 72h cooldown, unpatched

    complete_response = client.post(f"/api/v1/withdrawals/{request_id}/complete", headers=headers)
    assert complete_response.status_code == 409


def test_hard_lock_withdrawal_not_cancellable_after_approval(client, make_user, auth_headers, db_session):
    user = make_user()
    goal = _make_funded_goal(db_session, user, lock_type="HARD", saved="300.00")
    contact_id = _add_contact(client, auth_headers(user))
    headers = auth_headers(user)

    body = client.post(
        "/api/v1/withdrawals",
        json={
            "goal_id": str(goal.id),
            "emergency_contact_id": contact_id,
            "amount": "50.00",
            "reason": "OTHER",
        },
        headers=headers,
    ).json()
    request_id, otp = body["id"], body["debug_otp"]

    client.post(f"/api/v1/withdrawals/{request_id}/approve", json={"otp": otp})

    cancel_response = client.post(f"/api/v1/withdrawals/{request_id}/cancel", headers=headers)
    assert cancel_response.status_code == 409


def test_pending_withdrawal_is_cancellable(client, make_user, auth_headers, db_session):
    user = make_user()
    goal = _make_funded_goal(db_session, user, lock_type="MEDIUM", saved="300.00")
    contact_id = _add_contact(client, auth_headers(user))
    headers = auth_headers(user)

    body = client.post(
        "/api/v1/withdrawals",
        json={
            "goal_id": str(goal.id),
            "emergency_contact_id": contact_id,
            "amount": "50.00",
            "reason": "OTHER",
        },
        headers=headers,
    ).json()

    cancel_response = client.post(f"/api/v1/withdrawals/{body['id']}/cancel", headers=headers)
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "CANCELLED"
