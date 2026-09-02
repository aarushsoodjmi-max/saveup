"""Import every model here so ``Base.metadata`` is fully populated.

Alembic's ``env.py`` imports this package (indirectly, via
``app.models.user`` historically and now via this ``__init__``) to
build ``target_metadata`` for autogeneration and offline migrations.
Anything not imported here is invisible to Alembic.
"""

from app.models.achievement import Achievement, UserAchievement
from app.models.emergency_contact import EmergencyContact
from app.models.goal import Goal
from app.models.notification import Notification
from app.models.payment import PaymentAttempt, PaymentOrder
from app.models.refresh_token import RefreshToken
from app.models.streak import Streak
from app.models.transaction import Transaction
from app.models.user import User
from app.models.withdrawal_request import WithdrawalRequest

__all__ = [
    "Achievement",
    "UserAchievement",
    "EmergencyContact",
    "Goal",
    "Notification",
    "PaymentAttempt",
    "PaymentOrder",
    "RefreshToken",
    "Streak",
    "Transaction",
    "User",
    "WithdrawalRequest",
]
