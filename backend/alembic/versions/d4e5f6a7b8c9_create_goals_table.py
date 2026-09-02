"""create goals table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-27 09:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.uuid_type import UUIDType


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'goals',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('user_id', UUIDType(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('goal_image', sa.String(length=500), nullable=True),
        sa.Column('target_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('saved_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('monthly_target', sa.Numeric(12, 2), nullable=True),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('lock_type', sa.Enum('EASY', 'MEDIUM', 'HARD', name='goal_lock_type'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED', name='goal_status'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('target_amount > 0', name='ck_goals_target_amount_positive'),
        sa.CheckConstraint('saved_amount >= 0', name='ck_goals_saved_amount_non_negative'),
    )
    op.create_index('ix_goals_user_id', 'goals', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_goals_user_id', table_name='goals')
    op.drop_table('goals')
