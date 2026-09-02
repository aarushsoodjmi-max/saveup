"""add role to users

Revision ID: a1b2c3d4e5f6
Revises: 90efce4a924b
Create Date: 2026-08-27 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '90efce4a924b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'role',
            sa.Enum('USER', 'ADMIN', name='user_role'),
            nullable=False,
            server_default='USER',
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'role')
