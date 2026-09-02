"""The core financial ledger service.

Every money-moving operation in SaveUp funnels through this module:
manual deposits, payment-gateway-confirmed deposits, emergency
withdrawals, and refunds. The invariants it enforces:

1. **Decimal only.** Amounts are ``decimal.Decimal`` end to end (MySQL
   ``NUMERIC`` columns round-trip as ``Decimal`` via PyMySQL) -- never
   float.
2. **Row locking.** Every mutation starts with
   ``SELECT ... FOR UPDATE`` on the target ``Goal`` row
   (:meth:`GoalRepository.get_locked`), so two concurrent requests
   against the same goal serialize at the database instead of racing
   on ``saved_amount`` (classic lost-update bug).
3. **Atomicity.** The balance mutation and the ledger row insert happen
   in the same DB transaction and commit together -- if either fails,
   both roll back, so the ledger and the goal balance can never drift
   apart.
4. **Idempotency.** Callers may pass an ``idempotency_key``. A fast
   pre-check avoids duplicate work; the real guarantee is the
   ``UNIQUE`` constraint on ``transactions.idempotency_key`` -- if two
   concurrent requests both pass the pre-check, only one insert
   succeeds and the loser re-reads and returns the winner's row
   instead of erroring.
5. **No negative balances.** A withdrawal (or refund) that would push
   ``saved_amount`` below zero is rejected with
   :class:`InsufficientBalanceError` before anything is written.
6. **Resilience to transient write conflicts.** A handful of MySQL
   errors are expected, recoverable byproducts of real concurrent
   access to a locked row -- 1020 ("Record has changed since last
   read"), 1213 (deadlock), 1205 (lock wait timeout) -- rather than
   genuine failures. The whole locked operation (re-acquire the lock,
   re-check idempotency, re-apply) is retried with exponential backoff
   (see :func:`_run_with_retry`) instead of surfacing these to the
   caller. This adds resilience on top of -- never in place of -- the
   row locking and idempotency guarantees above: a retry re-enters the
   exact same locked/idempotent code path from the top, it doesn't skip
   or shortcut it.
"""

import logging
import random
import time
from decimal import Decimal
from typing import Callable, TypeVar
from uuid import UUID

from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, InsufficientBalanceError, NotFoundError
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.goal_repository import GoalRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.goal_service import GoalService

logger = logging.getLogger("saveup.ledger")

T = TypeVar("T")

# MySQL error codes that represent a transient write conflict on a
# locked row rather than a genuine failure -- safe (and necessary, for
# correctness under real concurrency) to retry from scratch.
#   1020 ER_CHECKREAD       "Record has changed since last read"
#   1213 ER_LOCK_DEADLOCK   deadlock found when trying to get lock
#   1205 ER_LOCK_WAIT_TIMEOUT  lock wait timeout exceeded
RETRYABLE_MYSQL_ERROR_CODES = frozenset({1020, 1213, 1205})


def _mysql_error_code(exc: DBAPIError) -> int | None:
    """Best-effort extraction of the numeric MySQL error code from a
    SQLAlchemy ``DBAPIError``'s wrapped driver exception. Returns
    ``None`` if it can't be determined (e.g. a different DB driver),
    in which case the error is treated as non-retryable.
    """
    orig = getattr(exc, "orig", None)
    args = getattr(orig, "args", None) if orig is not None else None
    if not args:
        return None
    code = args[0]
    return code if isinstance(code, int) else None


class LedgerService:
    def __init__(self, db: Session):
        self.db = db
        self.goal_repo = GoalRepository(db)
        self.transaction_repo = TransactionRepository(db)

    # ------------------------------------------------------------------
    def _run_with_retry(self, operation: Callable[[], T]) -> T:
        """Runs ``operation`` (a full locked-read-mutate-commit cycle),
        retrying with exponential backoff if it fails with one of
        :data:`RETRYABLE_MYSQL_ERROR_CODES`. Any other exception --
        including the ``IntegrityError`` path already handled inline by
        :meth:`_commit_or_return_existing` -- propagates immediately,
        unchanged.

        Rolling back before each retry is required: after a DBAPI error
        the session's current transaction is unusable until rolled
        back. Retrying re-enters ``operation`` from the top, so it
        re-acquires the row lock and re-checks idempotency fresh --
        never resumes partway through -- which is what keeps this safe
        to layer on top of those guarantees rather than around them.
        """
        max_attempts = max(settings.ledger_retry_max_attempts, 0) + 1
        base_backoff = settings.ledger_retry_base_backoff_seconds

        attempt = 0
        while True:
            try:
                return operation()
            except DBAPIError as exc:
                code = _mysql_error_code(exc)
                attempt += 1
                if code not in RETRYABLE_MYSQL_ERROR_CODES or attempt >= max_attempts:
                    raise
                self.db.rollback()
                backoff = base_backoff * (2 ** (attempt - 1)) + random.uniform(0, base_backoff)
                logger.warning(
                    "Retryable MySQL error %s on ledger operation (attempt %d/%d); "
                    "retrying in %.3fs",
                    code,
                    attempt,
                    max_attempts - 1,
                    backoff,
                )
                time.sleep(backoff)

    def _check_idempotent_replay(self, idempotency_key: str | None) -> Transaction | None:
        if not idempotency_key:
            return None
        return self.transaction_repo.get_by_idempotency_key(idempotency_key)

    def _commit_or_return_existing(
        self, transaction: Transaction, idempotency_key: str | None
    ) -> Transaction:
        try:
            self.transaction_repo.create(transaction)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if idempotency_key:
                existing = self.transaction_repo.get_by_idempotency_key(idempotency_key)
                if existing:
                    return existing
            raise ConflictError("This transaction has already been processed") from None
        self.db.refresh(transaction)
        return transaction

    def _load_owned_goal_locked(self, goal_id: UUID, user_id: UUID) -> Goal:
        goal = self.goal_repo.get_locked(goal_id)
        if goal is None or goal.user_id != user_id:
            raise NotFoundError("Goal not found")
        return goal

    def apply_deposit_locked(
        self,
        *,
        goal: Goal,
        user_id: UUID,
        amount: Decimal,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        idempotency_key: str | None = None,
        metadata: dict | None = None,
    ) -> Transaction:
        """Mutates an *already row-locked* goal and stages a Transaction
        row (added + flushed, not committed). Exposed so callers that
        need the deposit to be atomic with another write in the same
        request -- e.g. :class:`PaymentService` setting
        ``PaymentOrder.status = "PAID"`` -- can share one commit instead
        of the deposit committing on its own first. Ordinary callers
        should use :meth:`deposit` instead, which handles locking,
        idempotency, retrying, and committing end to end.
        """
        if goal.status != "ACTIVE":
            raise ConflictError(f"Cannot deposit into a goal with status {goal.status}")

        goal.saved_amount = goal.saved_amount + amount
        GoalService.mark_completed_if_reached(goal)

        transaction = Transaction(
            user_id=user_id,
            goal_id=goal.id,
            transaction_type="DEPOSIT",
            amount=amount,
            status="SUCCESS",
            balance_after=goal.saved_amount,
            reference_type=reference_type,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            extra_metadata=metadata,
        )
        self.transaction_repo.create(transaction)
        return transaction

    # ------------------------------------------------------------------
    def deposit(
        self,
        *,
        user: User,
        goal_id: UUID,
        amount: Decimal,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        idempotency_key: str | None = None,
        metadata: dict | None = None,
    ) -> Transaction:
        return self._run_with_retry(
            lambda: self._deposit_once(
                user=user,
                goal_id=goal_id,
                amount=amount,
                reference_type=reference_type,
                reference_id=reference_id,
                idempotency_key=idempotency_key,
                metadata=metadata,
            )
        )

    def _deposit_once(
        self,
        *,
        user: User,
        goal_id: UUID,
        amount: Decimal,
        reference_type: str | None,
        reference_id: UUID | None,
        idempotency_key: str | None,
        metadata: dict | None,
    ) -> Transaction:
        replay = self._check_idempotent_replay(idempotency_key)
        if replay is not None:
            return replay

        goal = self._load_owned_goal_locked(goal_id, user.id)
        transaction = self.apply_deposit_locked(
            goal=goal,
            user_id=user.id,
            amount=amount,
            reference_type=reference_type,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            metadata=metadata,
        )
        return self._commit_or_return_existing(transaction, idempotency_key)

    def apply_withdrawal_locked(
        self,
        *,
        goal: Goal,
        user_id: UUID,
        amount: Decimal,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        idempotency_key: str | None = None,
        metadata: dict | None = None,
    ) -> Transaction:
        """Symmetric counterpart to :meth:`apply_deposit_locked` for
        withdrawals -- see that method's docstring for why this exists
        as a separate, non-committing step.
        """
        if amount > goal.saved_amount:
            raise InsufficientBalanceError(
                "Withdrawal amount exceeds the goal's saved balance",
                details={
                    "saved_amount": str(goal.saved_amount),
                    "requested_amount": str(amount),
                },
            )

        goal.saved_amount = goal.saved_amount - amount
        if goal.status == "COMPLETED" and goal.saved_amount < goal.target_amount:
            goal.status = "ACTIVE"
            goal.completed_at = None

        transaction = Transaction(
            user_id=user_id,
            goal_id=goal.id,
            transaction_type="WITHDRAWAL",
            amount=amount,
            status="SUCCESS",
            balance_after=goal.saved_amount,
            reference_type=reference_type,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            extra_metadata=metadata,
        )
        self.transaction_repo.create(transaction)
        return transaction

    # ------------------------------------------------------------------
    def withdraw(
        self,
        *,
        user: User,
        goal_id: UUID,
        amount: Decimal,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        idempotency_key: str | None = None,
        metadata: dict | None = None,
    ) -> Transaction:
        return self._run_with_retry(
            lambda: self._withdraw_once(
                user=user,
                goal_id=goal_id,
                amount=amount,
                reference_type=reference_type,
                reference_id=reference_id,
                idempotency_key=idempotency_key,
                metadata=metadata,
            )
        )

    def _withdraw_once(
        self,
        *,
        user: User,
        goal_id: UUID,
        amount: Decimal,
        reference_type: str | None,
        reference_id: UUID | None,
        idempotency_key: str | None,
        metadata: dict | None,
    ) -> Transaction:
        replay = self._check_idempotent_replay(idempotency_key)
        if replay is not None:
            return replay

        goal = self._load_owned_goal_locked(goal_id, user.id)
        transaction = self.apply_withdrawal_locked(
            goal=goal,
            user_id=user.id,
            amount=amount,
            reference_type=reference_type,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            metadata=metadata,
        )
        return self._commit_or_return_existing(transaction, idempotency_key)

    # ------------------------------------------------------------------
    def refund_deposit(
        self,
        *,
        transaction_id: UUID,
        idempotency_key: str | None = None,
        metadata: dict | None = None,
    ) -> Transaction:
        """Reverses a previously SUCCESSful deposit (e.g. a payment
        gateway chargeback). Decreases the goal balance back down and
        marks the original transaction REVERSED so it's excluded from
        future refund attempts.
        """
        return self._run_with_retry(
            lambda: self._refund_deposit_once(
                transaction_id=transaction_id,
                idempotency_key=idempotency_key,
                metadata=metadata,
            )
        )

    def _refund_deposit_once(
        self,
        *,
        transaction_id: UUID,
        idempotency_key: str | None,
        metadata: dict | None,
    ) -> Transaction:
        replay = self._check_idempotent_replay(idempotency_key)
        if replay is not None:
            return replay

        original = self.transaction_repo.get_by_id(transaction_id)
        if original is None:
            raise NotFoundError("Transaction not found")
        if original.transaction_type != "DEPOSIT" or original.status != "SUCCESS":
            raise ConflictError("Only a successful deposit can be refunded")

        goal = self.goal_repo.get_locked(original.goal_id)
        if goal is None:
            raise NotFoundError("Goal not found")

        if original.amount > goal.saved_amount:
            raise InsufficientBalanceError(
                "Goal balance is insufficient to process this refund "
                "(funds may have already been withdrawn)",
                details={"saved_amount": str(goal.saved_amount), "refund_amount": str(original.amount)},
            )

        goal.saved_amount = goal.saved_amount - original.amount
        if goal.status == "COMPLETED":
            goal.status = "ACTIVE"
            goal.completed_at = None

        original.status = "REVERSED"

        refund_txn = Transaction(
            user_id=original.user_id,
            goal_id=goal.id,
            transaction_type="REFUND",
            amount=original.amount,
            status="SUCCESS",
            balance_after=goal.saved_amount,
            reference_type="transaction",
            reference_id=original.id,
            idempotency_key=idempotency_key,
            extra_metadata=metadata,
        )
        return self._commit_or_return_existing(refund_txn, idempotency_key)

    # ------------------------------------------------------------------
    def get_transaction_for_user(self, transaction_id: UUID, user: User) -> Transaction:
        transaction = self.transaction_repo.get_by_id(transaction_id)
        if transaction is None or transaction.user_id != user.id:
            raise NotFoundError("Transaction not found")
        return transaction

    def list_for_user(
        self,
        user: User,
        *,
        offset: int,
        limit: int,
        goal_id: UUID | None = None,
        transaction_type: str | None = None,
    ) -> tuple[list[Transaction], int]:
        return self.transaction_repo.list_for_user(
            user.id, offset=offset, limit=limit, goal_id=goal_id, transaction_type=transaction_type
        )
