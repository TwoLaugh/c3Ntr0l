"""proposed changes

Revision ID: 0005_proposed_changes
Revises: 0004_daily_plan_items_item_link
Create Date: 2026-05-29
"""

from alembic import op

revision = "0005_proposed_changes"
down_revision = "0004_daily_plan_items_item_link"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE proposed_change_type AS ENUM "
        "('insert_item_today', 'move_today_item', 'defer_today_item', 'regenerate_today')"
    )
    op.execute("CREATE TYPE proposed_change_status AS ENUM ('pending', 'accepted', 'rejected', 'expired')")
    op.execute(
        """
        CREATE TABLE proposed_changes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_type source_type NOT NULL DEFAULT 'ai',
            source_id UUID,
            change_type proposed_change_type NOT NULL,
            status proposed_change_status NOT NULL DEFAULT 'pending',
            title TEXT NOT NULL,
            rationale TEXT,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            result JSONB,
            decided_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_proposed_changes_user_status ON proposed_changes(user_id, status, created_at DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_proposed_changes_user_status")
    op.execute("DROP TABLE IF EXISTS proposed_changes")
    op.execute("DROP TYPE IF EXISTS proposed_change_status")
    op.execute("DROP TYPE IF EXISTS proposed_change_type")
