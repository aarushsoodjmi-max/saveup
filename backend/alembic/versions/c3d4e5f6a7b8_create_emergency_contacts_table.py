"""create emergency_contacts table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-27 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.uuid_type import UUIDType


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'emergency_contacts',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('user_id', UUIDType(), nullable=False),
        sa.Column('contact_name', sa.String(length=100), nullable=False),
        sa.Column('relationship_label', sa.String(length=50), nullable=False),
        sa.Column('phone_number', sa.String(length=16), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_emergency_contacts_user_id', 'emergency_contacts', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_emergency_contacts_user_id', table_name='emergency_contacts')
    op.drop_table('emergency_contacts')
