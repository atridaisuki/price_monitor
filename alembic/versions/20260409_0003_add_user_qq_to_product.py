"""add user_qq to product

Revision ID: 20260409_0003
Revises: 20260408_0002
Create Date: 2026-04-09 00:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260409_0003"
down_revision = "20260408_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product", sa.Column("user_qq", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("product", "user_qq")
