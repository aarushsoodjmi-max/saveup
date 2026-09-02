"""create payment_attempts table

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-27 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.uuid_type import UUIDType


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payment_attempts',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('payment_order_id', UUIDType(), nullable=False),
        sa.Column('provider_payment_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('INITIATED', 'SUCCESS', 'FAILED', name='payment_attempt_status'), nullable=False),
        sa.Column('signature', sa.String(length=255), nullable=True),
        sa.Column('signature_valid', sa.Boolean(), nullable=True),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['payment_order_id'], ['payment_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payment_attempts_payment_order_id', 'payment_attempts', ['payment_order_id'])


def downgrade() -> None:
    op.drop_index('ix_payment_attempts_payment_order_id', table_name='payment_attempts')
    op.drop_table('payment_attempts')
