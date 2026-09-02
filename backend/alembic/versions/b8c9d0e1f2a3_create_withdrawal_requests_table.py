"""create withdrawal_requests table

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-08-27 09:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.uuid_type import UUIDType


# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'withdrawal_requests',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('user_id', UUIDType(), nullable=False),
        sa.Column('goal_id', UUIDType(), nullable=False),
        sa.Column('emergency_contact_id', UUIDType(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('reason', sa.Enum('MEDICAL', 'FAMILY', 'JOB_LOSS', 'EDUCATION', 'OTHER', name='withdrawal_reason'), nullable=False),
        sa.Column('reason_notes', sa.String(length=500), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'COOLDOWN', 'COMPLETED', 'FAILED', 'CANCELLED', name='withdrawal_status'), nullable=False),
        sa.Column('otp_hash', sa.String(length=64), nullable=True),
        sa.Column('otp_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('otp_attempts', sa.Integer(), nullable=False),
        sa.Column('cooldown_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('transaction_id', UUIDType(), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['emergency_contact_id'], ['emergency_contacts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount > 0', name='ck_withdrawal_requests_amount_positive'),
    )
    op.create_index('ix_withdrawal_requests_user_id', 'withdrawal_requests', ['user_id'])
    op.create_index('ix_withdrawal_requests_goal_id', 'withdrawal_requests', ['goal_id'])


def downgrade() -> None:
    op.drop_index('ix_withdrawal_requests_goal_id', table_name='withdrawal_requests')
    op.drop_index('ix_withdrawal_requests_user_id', table_name='withdrawal_requests')
    op.drop_table('withdrawal_requests')
