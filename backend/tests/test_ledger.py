"""The ledger: the most safety-critical module in the app.

These tests exercise real concurrent DB sessions/threads against the
live MySQL test database so the ``SELECT ... FOR UPDATE`` row locking
is actually engaged -- an in-memory/SQLite backend would silently skip
locking and let these tests pass for the wrong reason.
"""

import threading
from decimal import Decimal

import pytest

from app.core.exceptions import ConflictError, InsufficientBalanceError, NotFoundError
from app.models.goal import Goal
from app.services.ledger_service import LedgerService


def _make_goal(db_session, user, *, target="1000.00", saved="0.00", lock_type="EASY", status="ACTIVE"):
    goal = Goal(
        user_id=user.id,
        title="Test Goal",
        category="General",
        target_amount=Decimal(target),
        saved_amount=Decimal(saved),
        lock_type=lock_type,
        status=status,
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    return goal


def test_deposit_increases_saved_amount_with_decimal_precision(db_session, make_user):
    user = make_user()
    goal = _make_goal(db_session, user)

    txn = LedgerService(db_session).deposit(user=user, goal_id=goal.id, amount=Decimal("123.45"))

    assert txn.status == "SUCCESS"
    assert txn.balance_after == Decimal("123.45")
    db_session.refresh(goal)
    assert goal.saved_amount == Decimal("123.45")
    assert isinstance(goal.saved_amount, Decimal)


def test_deposit_marks_goal_completed_when_target_reached(db_session, make_user):
    user = make_user()
    goal = _make_goal(db_session, user, target="100.00", saved="90.00")

    LedgerService(db_session).deposit(user=user, goal_id=goal.id, amount=Decimal("10.00"))

    db_session.refresh(goal)
    assert goal.status == "COMPLETED"
    assert goal.completed_at is not None


def test_deposit_rejected_for_non_active_goal(db_session, make_user):
    user = make_user()
    goal = _make_goal(db_session, user, status="PAUSED")

    with pytest.raises(ConflictError):
        LedgerService(db_session).deposit(user=user, goal_id=goal.id, amount=Decimal("10.00"))


def test_deposit_rejected_for_other_users_goal(db_session, make_user):
    owner = make_user()
    intruder = make_user()
    goal = _make_goal(db_session, owner)

    with pytest.raises(NotFoundError):
        LedgerService(db_session).deposit(user=intruder, goal_id=goal.id, amount=Decimal("10.00"))


def test_withdrawal_rejects_amount_exceeding_balance(db_session, make_user):
    user = make_user()
    goal = _make_goal(db_session, user, saved="50.00")

    with pytest.raises(InsufficientBalanceError):
        LedgerService(db_session).withdraw(user=user, goal_id=goal.id, amount=Decimal("50.01"))

    db_session.refresh(goal)
    assert goal.saved_amount == Decimal("50.00")  # untouched


def test_withdrawal_never_goes_negative(db_session, make_user):
    user = make_user()
    goal = _make_goal(db_session, user, saved="50.00")

    LedgerService(db_session).withdraw(user=user, goal_id=goal.id, amount=Decimal("50.00"))

    db_session.refresh(goal)
    assert goal.saved_amount == Decimal("0.00")
    assert goal.saved_amount >= 0


def test_deposit_idempotency_key_prevents_duplicate_processing(db_session, make_user):
    user = make_user()
    goal = _make_goal(db_session, user)

    service = LedgerService(db_session)
    txn1 = service.deposit(user=user, goal_id=goal.id, amount=Decimal("25.00"), idempotency_key="fixed-key-1")
    txn2 = service.deposit(user=user, goal_id=goal.id, amount=Decimal("25.00"), idempotency_key="fixed-key-1")

    assert txn1.id == txn2.id
    db_session.refresh(goal)
    assert goal.saved_amount == Decimal("25.00")  # only applied once


def test_refund_reverses_a_deposit(db_session, make_user):
    user = make_user()
    goal = _make_goal(db_session, user)

    service = LedgerService(db_session)
    deposit_txn = service.deposit(user=user, goal_id=goal.id, amount=Decimal("40.00"))
    refund_txn = service.refund_deposit(transaction_id=deposit_txn.id)

    assert refund_txn.transaction_type == "REFUND"
    assert refund_txn.amount == Decimal("40.00")
    db_session.refresh(goal)
    assert goal.saved_amount == Decimal("0.00")

    db_session.refresh(deposit_txn)
    assert deposit_txn.status == "REVERSED"


# ----------------------------------------------------------------------
# Concurrency: the whole reason for SELECT ... FOR UPDATE
# ----------------------------------------------------------------------


def test_concurrent_deposits_do_not_lose_updates(session_factory, make_user):
    """Two threads, two independent DB sessions/connections, depositing
    into the SAME goal at the same time. Without row locking this is
    the textbook lost-update race: both read saved_amount=0, both
    compute 0+50, both write 50 -- final balance 50 instead of 100.
    """
    user = make_user()
    setup_session = session_factory()
    goal = _make_goal(setup_session, user)
    goal_id = goal.id
    setup_session.close()

    errors: list[Exception] = []

    def _deposit():
        session = session_factory()
        try:
            LedgerService(session).deposit(user=user, goal_id=goal_id, amount=Decimal("50.00"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            session.close()

    threads = [threading.Thread(target=_deposit) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Unexpected errors: {errors}"

    verify_session = session_factory()
    final_goal = verify_session.get(Goal, goal_id)
    assert final_goal.saved_amount == Decimal("100.00")
    verify_session.close()


def test_concurrent_withdrawals_never_overdraw(session_factory, make_user):
    """Two threads each try to withdraw 80 from a goal holding 100.
    Exactly one must succeed; the other must see the post-withdrawal
    balance and be rejected -- never both succeeding (which would leave
    a negative balance).
    """
    user = make_user()
    setup_session = session_factory()
    goal = _make_goal(setup_session, user, saved="100.00")
    goal_id = goal.id
    setup_session.close()

    results: list[str] = []
    lock = threading.Lock()

    def _withdraw():
        session = session_factory()
        try:
            LedgerService(session).withdraw(user=user, goal_id=goal_id, amount=Decimal("80.00"))
            with lock:
                results.append("success")
        except InsufficientBalanceError:
            with lock:
                results.append("rejected")
        finally:
            session.close()

    threads = [threading.Thread(target=_withdraw) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == ["rejected", "success"]

    verify_session = session_factory()
    final_goal = verify_session.get(Goal, goal_id)
    assert final_goal.saved_amount == Decimal("20.00")
    assert final_goal.saved_amount >= 0
    verify_session.close()


def test_concurrent_duplicate_idempotency_key_only_applies_once(session_factory, make_user):
    """Simulates two near-simultaneous retries of the exact same
    request (same idempotency key). The DB UNIQUE constraint -- not
    just the in-process pre-check -- must be what prevents the double
    apply, since both threads can pass the pre-check before either
    commits.
    """
    user = make_user()
    setup_session = session_factory()
    goal = _make_goal(setup_session, user)
    goal_id = goal.id
    setup_session.close()

    txns: list = []
    lock = threading.Lock()

    def _deposit():
        session = session_factory()
        try:
            txn = LedgerService(session).deposit(
                user=user, goal_id=goal_id, amount=Decimal("30.00"), idempotency_key="race-key"
            )
            with lock:
                txns.append(txn.id)
        finally:
            session.close()

    threads = [threading.Thread(target=_deposit) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(set(txns)) == 1  # both threads converge on the same transaction id

    verify_session = session_factory()
    final_goal = verify_session.get(Goal, goal_id)
    assert final_goal.saved_amount == Decimal("30.00")  # applied exactly once
    verify_session.close()
