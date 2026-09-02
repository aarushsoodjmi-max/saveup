"""Emergency withdrawal workflow for MEDIUM/HARD lock goals.

    PENDING --(contact approves w/ OTP)--> APPROVED -> COOLDOWN --(cooldown elapses)--> COMPLETED
       |                                                  |
       +--(contact rejects w/ OTP)--> REJECTED             +--(release fails)--> FAILED
       |
       +--(user cancels, EASY/MEDIUM only, pre-completion)--> CANCELLED

EASY lock goals never enter this workflow -- they're withdrawn
directly through the ledger (``LedgerService.withdraw``) since they
carry no lock guarantee to begin with.

The OTP proving contact approval/rejection is sent to the *emergency
contact's* phone, not the account owner's, and is verified through an
endpoint that intentionally does not require the account owner's JWT
(the contact has no SaveUp account of their own) -- knowledge of the
request's UUID plus the one-time OTP is the credential.
"""

from datetime import timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import LOCK_TYPE_COOLDOWN_HOURS, LOCK_TYPES_CANCELLABLE_AFTER_APPROVAL
from app.core.exceptions import (
    ConflictError,
    InsufficientBalanceError,
    InvalidOTPError,
    NotFoundError,
    OTPExpiredError,
)
from app.core.security import generate_otp, hash_otp, verify_otp_hash
from app.core.time_utils import ensure_aware, utc_now
from app.models.user import User
from app.models.withdrawal_request import WithdrawalRequest
from app.repositories.emergency_contact_repository import EmergencyContactRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.withdrawal_repository import WithdrawalRepository
from app.schemas.withdrawal import WithdrawalRequestCreate
from app.services.ledger_service import LedgerService
from app.services.notification_service import NotificationService
from app.services.sms_provider import SMSProvider, sms_provider as default_sms_provider


class WithdrawalService:
    def __init__(self, db: Session, sms: SMSProvider = default_sms_provider):
        self.db = db
        self.sms = sms
        self.repo = WithdrawalRepository(db)
        self.goal_repo = GoalRepository(db)
        self.contact_repo = EmergencyContactRepository(db)
        self.ledger_service = LedgerService(db)
        self.notification_service = NotificationService(db)

    # ------------------------------------------------------------------
    def _issue_otp(self, request: WithdrawalRequest, contact_phone: str, contact_name: str) -> str | None:
        otp = generate_otp()
        request.otp_hash = hash_otp(contact_phone, otp)
        request.otp_expires_at = utc_now() + timedelta(seconds=settings.otp_expire_seconds)
        request.otp_attempts = 0
        self.db.commit()

        self.sms.send(
            contact_phone,
            f"SaveUp: You've been asked to approve an emergency withdrawal "
            f"request (₹{request.amount}). Your verification code is {otp}. "
            f"It expires in {settings.otp_expire_seconds // 60} minutes.",
        )
        return otp if (settings.otp_debug_expose and not settings.is_production) else None

    def _verify_otp(self, request: WithdrawalRequest, contact_phone: str, otp: str) -> None:
        if request.otp_hash is None or request.otp_expires_at is None:
            raise OTPExpiredError("No active OTP for this request; ask for a new one")
        if ensure_aware(request.otp_expires_at) < utc_now():
            raise OTPExpiredError("OTP has expired")
        if request.otp_attempts >= settings.otp_max_attempts:
            raise InvalidOTPError("Too many incorrect attempts; this request must be re-issued")

        if not verify_otp_hash(contact_phone, otp, request.otp_hash):
            request.otp_attempts += 1
            self.db.commit()
            raise InvalidOTPError("Incorrect OTP")

        # One-time use.
        request.otp_hash = None
        request.otp_expires_at = None

    # ------------------------------------------------------------------
    def request_withdrawal(
        self, user: User, payload: WithdrawalRequestCreate
    ) -> tuple[WithdrawalRequest, str | None]:
        goal = self.goal_repo.get_for_user(payload.goal_id, user.id)
        if goal is None:
            raise NotFoundError("Goal not found")

        if goal.lock_type == "EASY":
            raise ConflictError(
                "EASY lock goals can be withdrawn directly via the deposit/withdrawal "
                "endpoint; the emergency workflow only applies to MEDIUM and HARD lock goals"
            )

        if payload.amount > goal.saved_amount:
            raise InsufficientBalanceError(
                "Requested amount exceeds the goal's saved balance",
                details={"saved_amount": str(goal.saved_amount)},
            )

        contact = self.contact_repo.get_for_user(payload.emergency_contact_id, user.id)
        if contact is None:
            raise NotFoundError("Emergency contact not found")

        if self.repo.get_open_for_goal(goal.id) is not None:
            raise ConflictError("There is already an active withdrawal request for this goal")

        request = WithdrawalRequest(
            user_id=user.id,
            goal_id=goal.id,
            emergency_contact_id=contact.id,
            amount=payload.amount,
            reason=payload.reason,
            reason_notes=payload.reason_notes,
            status="PENDING",
        )
        self.repo.create(request)
        self.db.commit()
        self.db.refresh(request)

        debug_otp = self._issue_otp(request, contact.phone_number, contact.contact_name)
        self.notification_service.notify_withdrawal_event(
            user_id=user.id, goal_title=goal.title, status="PENDING"
        )
        return request, debug_otp

    def resend_otp(self, user: User, request_id: UUID) -> str | None:
        request = self.repo.get_for_user(request_id, user.id)
        if request is None:
            raise NotFoundError("Withdrawal request not found")
        if request.status != "PENDING":
            raise ConflictError(f"Cannot resend an approval code for a request with status {request.status}")

        contact = self.contact_repo.get_for_user(request.emergency_contact_id, user.id)
        if contact is None:
            raise NotFoundError("Emergency contact not found")

        return self._issue_otp(request, contact.phone_number, contact.contact_name)

    # ------------------------------------------------------------------
    def approve_withdrawal(self, request_id: UUID, otp: str) -> WithdrawalRequest:
        request = self.repo.get_locked(request_id)
        if request is None:
            raise NotFoundError("Withdrawal request not found")
        if request.status != "PENDING":
            raise ConflictError(f"Cannot approve a request with status {request.status}")

        contact = self.contact_repo.get_for_user(request.emergency_contact_id, request.user_id)
        if contact is None:
            raise NotFoundError("Emergency contact not found")

        self._verify_otp(request, contact.phone_number, otp)

        goal = self.goal_repo.get_by_id(request.goal_id)
        cooldown_hours = LOCK_TYPE_COOLDOWN_HOURS.get(goal.lock_type, 0) if goal else 0

        request.approved_at = utc_now()
        if cooldown_hours > 0:
            request.status = "COOLDOWN"
            request.cooldown_ends_at = utc_now() + timedelta(hours=cooldown_hours)
        else:
            request.status = "APPROVED"

        self.db.commit()
        self.db.refresh(request)

        if goal is not None:
            self.notification_service.notify_withdrawal_event(
                user_id=request.user_id, goal_title=goal.title, status=request.status
            )
        return request

    def reject_withdrawal(self, request_id: UUID, otp: str, rejection_reason: str) -> WithdrawalRequest:
        request = self.repo.get_locked(request_id)
        if request is None:
            raise NotFoundError("Withdrawal request not found")
        if request.status != "PENDING":
            raise ConflictError(f"Cannot reject a request with status {request.status}")

        contact = self.contact_repo.get_for_user(request.emergency_contact_id, request.user_id)
        if contact is None:
            raise NotFoundError("Emergency contact not found")

        self._verify_otp(request, contact.phone_number, otp)

        request.status = "REJECTED"
        request.rejection_reason = rejection_reason
        self.db.commit()
        self.db.refresh(request)

        goal = self.goal_repo.get_by_id(request.goal_id)
        if goal is not None:
            self.notification_service.notify_withdrawal_event(
                user_id=request.user_id, goal_title=goal.title, status="REJECTED"
            )
        return request

    # ------------------------------------------------------------------
    def cancel_withdrawal(self, user: User, request_id: UUID) -> WithdrawalRequest:
        request = self.repo.get_locked(request_id)
        if request is None or request.user_id != user.id:
            raise NotFoundError("Withdrawal request not found")

        goal = self.goal_repo.get_by_id(request.goal_id)
        lock_type = goal.lock_type if goal else "HARD"

        cancellable_statuses = {"PENDING"} | (
            {"APPROVED", "COOLDOWN"} if lock_type in LOCK_TYPES_CANCELLABLE_AFTER_APPROVAL else set()
        )
        if request.status not in cancellable_statuses:
            raise ConflictError(
                f"A {lock_type}-lock withdrawal cannot be cancelled once it reaches status {request.status}"
            )

        request.status = "CANCELLED"
        self.db.commit()
        self.db.refresh(request)

        if goal is not None:
            self.notification_service.notify_withdrawal_event(
                user_id=user.id, goal_title=goal.title, status="CANCELLED"
            )
        return request

    # ------------------------------------------------------------------
    def complete_withdrawal(self, user: User, request_id: UUID) -> WithdrawalRequest:
        """Releases the funds once the cooldown period has elapsed.
        Idempotent: calling this again after a successful completion
        just returns the already-completed request.
        """
        request = self.repo.get_locked(request_id)
        if request is None or request.user_id != user.id:
            raise NotFoundError("Withdrawal request not found")

        if request.status == "COMPLETED":
            return request

        if request.status == "COOLDOWN":
            if request.cooldown_ends_at is not None and ensure_aware(request.cooldown_ends_at) > utc_now():
                raise ConflictError(
                    "Withdrawal is still in its cooling-off period",
                    details={"cooldown_ends_at": request.cooldown_ends_at.isoformat()},
                )
        elif request.status != "APPROVED":
            raise ConflictError(f"Cannot complete a request with status {request.status}")

        goal = self.goal_repo.get_locked(request.goal_id)
        if goal is None:
            raise NotFoundError("Goal not found")

        idempotency_key = f"withdrawal_request:{request.id}"

        try:
            transaction = self.ledger_service.apply_withdrawal_locked(
                goal=goal,
                user_id=request.user_id,
                amount=request.amount,
                reference_type="withdrawal_request",
                reference_id=request.id,
                idempotency_key=idempotency_key,
            )
        except InsufficientBalanceError:
            request.status = "FAILED"
            self.db.commit()
            raise

        request.status = "COMPLETED"
        request.transaction_id = transaction.id
        request.completed_at = utc_now()

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self.ledger_service.transaction_repo.get_by_idempotency_key(idempotency_key)
            request = self.repo.get_by_id(request.id)
            if existing is not None and request is not None:
                request.status = "COMPLETED"
                request.transaction_id = existing.id
                request.completed_at = existing.created_at
                self.db.commit()

        self.db.refresh(request)
        self.notification_service.notify_withdrawal_event(
            user_id=request.user_id, goal_title=goal.title, status="COMPLETED"
        )
        return request

    # ------------------------------------------------------------------
    def admin_approve_withdrawal(self, request_id: UUID) -> WithdrawalRequest:
        """Support/ops override: an authenticated admin approves a stuck
        request directly (e.g. the emergency contact is unreachable).
        Skips OTP verification since the admin is already authenticated
        and authorized via RBAC, but still goes through the normal
        lock-type cooldown.
        """
        request = self.repo.get_locked(request_id)
        if request is None:
            raise NotFoundError("Withdrawal request not found")
        if request.status != "PENDING":
            raise ConflictError(f"Cannot approve a request with status {request.status}")

        goal = self.goal_repo.get_by_id(request.goal_id)
        cooldown_hours = LOCK_TYPE_COOLDOWN_HOURS.get(goal.lock_type, 0) if goal else 0

        request.approved_at = utc_now()
        if cooldown_hours > 0:
            request.status = "COOLDOWN"
            request.cooldown_ends_at = utc_now() + timedelta(hours=cooldown_hours)
        else:
            request.status = "APPROVED"

        self.db.commit()
        self.db.refresh(request)

        if goal is not None:
            self.notification_service.notify_withdrawal_event(
                user_id=request.user_id, goal_title=goal.title, status=request.status
            )
        return request

    def admin_reject_withdrawal(self, request_id: UUID, rejection_reason: str) -> WithdrawalRequest:
        request = self.repo.get_locked(request_id)
        if request is None:
            raise NotFoundError("Withdrawal request not found")
        if request.status not in ("PENDING", "APPROVED", "COOLDOWN"):
            raise ConflictError(f"Cannot reject a request with status {request.status}")

        request.status = "REJECTED"
        request.rejection_reason = rejection_reason
        self.db.commit()
        self.db.refresh(request)

        goal = self.goal_repo.get_by_id(request.goal_id)
        if goal is not None:
            self.notification_service.notify_withdrawal_event(
                user_id=request.user_id, goal_title=goal.title, status="REJECTED"
            )
        return request

    # ------------------------------------------------------------------
    def get_for_user(self, user: User, request_id: UUID) -> WithdrawalRequest:
        request = self.repo.get_for_user(request_id, user.id)
        if request is None:
            raise NotFoundError("Withdrawal request not found")
        return request

    def list_for_user(self, user: User, *, offset: int, limit: int) -> tuple[list[WithdrawalRequest], int]:
        return self.repo.list_for_user(user.id, offset=offset, limit=limit)
