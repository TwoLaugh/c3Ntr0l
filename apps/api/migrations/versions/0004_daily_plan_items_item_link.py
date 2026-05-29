"""link daily plan items to items

Revision ID: 0004_daily_plan_items_item_link
Revises: 0003_categories_items
Create Date: 2026-05-29
"""

from alembic import op

revision = "0004_daily_plan_items_item_link"
down_revision = "0003_categories_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE daily_plan_items ADD COLUMN item_id UUID REFERENCES items(id) ON DELETE SET NULL")
    op.execute("CREATE INDEX idx_daily_plan_items_item ON daily_plan_items(item_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_daily_plan_items_item")
    op.execute("ALTER TABLE daily_plan_items DROP COLUMN IF EXISTS item_id")
