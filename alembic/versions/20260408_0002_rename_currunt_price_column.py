"""rename currunt_price column

Revision ID: 20260408_0002
Revises: 20260408_0001
Create Date: 2026-04-09 00:08:00
"""

from alembic import op


revision = "20260408_0002"
down_revision = "20260408_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'product' AND column_name = 'currunt_price'
            ) AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'product' AND column_name = 'current_price'
            ) THEN
                ALTER TABLE product RENAME COLUMN currunt_price TO current_price;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'product' AND column_name = 'current_price'
            ) AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'product' AND column_name = 'currunt_price'
            ) THEN
                ALTER TABLE product RENAME COLUMN current_price TO currunt_price;
            END IF;
        END
        $$;
        """
    )
