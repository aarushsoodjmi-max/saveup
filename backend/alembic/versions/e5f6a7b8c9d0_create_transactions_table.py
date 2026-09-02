"""create transactions table (ledger)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-27 09:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.uuid_type import UUIDType


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'transactions',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('user_id', UUIDType(), nullable=False),
        sa.Column('goal_id', UUIDType(), nullable=False),
        sa.Column('transaction_type', sa.Enum('DEPOSIT', 'WITHDRAWAL', 'REFUND', name='transaction_type'), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', 'REVERSED', name='transaction_status'), nullable=False),
        sa.Column('balance_after', sa.Numeric(12, 2), nullable=True),
        sa.Column('reference_type', sa.String(length=30), nullable=True),
        sa.Column('reference_id', UUIDType(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key'),
        sa.CheckConstraint('amount > 0', name='ck_transactions_amount_positive'),
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_goal_id', 'transactions', ['goal_id'])
    op.create_index('ix_transactions_created_at', 'transactions', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_transactions_created_at', table_name='transactions')
    op.drop_index('ix_transactions_goal_id', table_name='transactions')
    op.drop_index('ix_transactions_user_id', table_name='transactions')
    op.drop_table('transactions')
