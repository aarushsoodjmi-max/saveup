"""create payment_orders table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-27 09:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.uuid_type import UUIDType


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payment_orders',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('user_id', UUIDType(), nullable=False),
        sa.Column('goal_id', UUIDType(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False),
        sa.Column('provider_order_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('CREATED', 'ATTEMPTED', 'PAID', 'FAILED', 'EXPIRED', name='payment_order_status'), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('transaction_id', UUIDType(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_order_id'),
        sa.UniqueConstraint('idempotency_key'),
        sa.CheckConstraint('amount > 0', name='ck_payment_orders_amount_positive'),
    )
    op.create_index('ix_payment_orders_user_id', 'payment_orders', ['user_id'])
    op.create_index('ix_payment_orders_goal_id', 'payment_orders', ['goal_id'])


def downgrade() -> None:
    op.drop_index('ix_payment_orders_goal_id', table_name='payment_orders')
    op.drop_index('ix_payment_orders_user_id', table_name='payment_orders')
    op.drop_table('payment_orders')
