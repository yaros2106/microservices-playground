"""add password hash to users

Revision ID: 80c21a9effad
Revises: d9b180022131
Create Date: 2026-10-23 12:35:27.566481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '80c21a9effad'
down_revision: Union[str, Sequence[str], None] = 'd9b180022131'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
