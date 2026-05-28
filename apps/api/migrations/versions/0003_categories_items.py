"""categories and items

Revision ID: 0003_categories_items
Revises: 0002_entries_context_sections
Create Date: 2026-05-28
"""

from alembic import op

revision = "0003_categories_items"
down_revision = "0002_entries_context_sections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE category_status AS ENUM ('active', 'archived')")
    op.execute("CREATE TYPE item_type AS ENUM ('action', 'reminder', 'routine', 'milestone', 'note', 'recurring_action')")
    op.execute("CREATE TYPE item_status AS ENUM ('active', 'completed', 'archived')")
    op.execute("CREATE TYPE item_priority AS ENUM ('low', 'normal', 'high', 'urgent')")
    op.execute("CREATE TYPE recurrence_status AS ENUM ('active', 'paused', 'archived')")
    op.execute(
        "CREATE TYPE item_event_type AS ENUM "
        "('complete', 'partial', 'skipped', 'moved', 'abandoned', 'reopened')"
    )

    op.execute(
        """
        CREATE TABLE categories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            status category_status NOT NULL DEFAULT 'active',
            sort_order INTEGER NOT NULL DEFAULT 0,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            archived_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (user_id, name)
        )
        """
    )
    op.execute("CREATE INDEX idx_categories_user_status ON categories(user_id, status)")

    op.execute(
        """
        CREATE TABLE items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            primary_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
            source_entry_id UUID REFERENCES entries(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            notes TEXT,
            item_type item_type NOT NULL DEFAULT 'action',
            status item_status NOT NULL DEFAULT 'active',
            priority item_priority NOT NULL DEFAULT 'normal',
            flags JSONB NOT NULL DEFAULT '[]'::jsonb,
            due_at TIMESTAMPTZ,
            do_window_start TIMESTAMPTZ,
            do_window_end TIMESTAMPTZ,
            effort_estimate_minutes INTEGER,
            energy_required energy_level,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            archived_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_items_user_status ON items(user_id, status)")
    op.execute("CREATE INDEX idx_items_user_category ON items(user_id, primary_category_id)")
    op.execute("CREATE INDEX idx_items_user_due_at ON items(user_id, due_at)")
    op.execute("CREATE INDEX idx_items_flags ON items USING GIN(flags)")

    op.execute(
        """
        CREATE TABLE item_recurrence (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            recurrence_rule TEXT NOT NULL,
            preferred_time_window JSONB NOT NULL DEFAULT '{}'::jsonb,
            status recurrence_status NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (item_id)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE item_context_links (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            context_section_id UUID NOT NULL REFERENCES context_sections(id) ON DELETE CASCADE,
            link_type TEXT NOT NULL DEFAULT 'related',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (item_id, context_section_id)
        )
        """
    )
    op.execute("CREATE INDEX idx_item_context_links_context ON item_context_links(context_section_id)")

    op.execute(
        """
        CREATE TABLE item_category_links (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            link_type TEXT NOT NULL DEFAULT 'related',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (item_id, category_id)
        )
        """
    )
    op.execute("CREATE INDEX idx_item_category_links_category ON item_category_links(category_id)")

    op.execute(
        """
        CREATE TABLE item_completion_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            plan_instance_id UUID,
            event_type item_event_type NOT NULL,
            note TEXT,
            amount_done TEXT,
            ai_interpretation JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_item_completion_events_item ON item_completion_events(item_id, created_at DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_item_completion_events_item")
    op.execute("DROP TABLE IF EXISTS item_completion_events")
    op.execute("DROP INDEX IF EXISTS idx_item_category_links_category")
    op.execute("DROP TABLE IF EXISTS item_category_links")
    op.execute("DROP INDEX IF EXISTS idx_item_context_links_context")
    op.execute("DROP TABLE IF EXISTS item_context_links")
    op.execute("DROP TABLE IF EXISTS item_recurrence")
    op.execute("DROP INDEX IF EXISTS idx_items_flags")
    op.execute("DROP INDEX IF EXISTS idx_items_user_due_at")
    op.execute("DROP INDEX IF EXISTS idx_items_user_category")
    op.execute("DROP INDEX IF EXISTS idx_items_user_status")
    op.execute("DROP TABLE IF EXISTS items")
    op.execute("DROP INDEX IF EXISTS idx_categories_user_status")
    op.execute("DROP TABLE IF EXISTS categories")

    op.execute("DROP TYPE IF EXISTS item_event_type")
    op.execute("DROP TYPE IF EXISTS recurrence_status")
    op.execute("DROP TYPE IF EXISTS item_priority")
    op.execute("DROP TYPE IF EXISTS item_status")
    op.execute("DROP TYPE IF EXISTS item_type")
    op.execute("DROP TYPE IF EXISTS category_status")
