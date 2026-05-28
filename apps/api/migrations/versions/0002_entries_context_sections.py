"""entries and context sections

Revision ID: 0002_entries_context_sections
Revises: 0001_initial_schema
Create Date: 2026-05-28
"""

from alembic import op

revision = "0002_entries_context_sections"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE entry_source AS ENUM "
        "('inbox', 'onboarding', 'daily_review', 'weekly_review', 'completion_note', 'manual_admin', 'integration')"
    )
    op.execute("CREATE TYPE entry_actor AS ENUM ('user', 'ai', 'system', 'integration')")
    op.execute(
        "CREATE TYPE context_section_type AS ENUM "
        "('general', 'health', 'person', 'category', 'planning_preference', 'capacity', "
        "'work', 'home', 'relationship', 'meaning', 'custom')"
    )
    op.execute("CREATE TYPE context_status AS ENUM ('active', 'archived')")
    op.execute("CREATE TYPE context_revision_source AS ENUM ('ai', 'user', 'system')")
    op.execute("CREATE TYPE confidence_level AS ENUM ('low', 'medium', 'high')")
    op.execute("CREATE TYPE ai_change_level AS ENUM ('silent', 'report', 'confirm')")

    op.execute(
        """
        CREATE TABLE entries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_type entry_source NOT NULL,
            source_id UUID,
            actor entry_actor NOT NULL DEFAULT 'user',
            raw_text TEXT NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            ai_interpretation JSONB,
            archived_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_entries_user_created ON entries(user_id, created_at DESC)")
    op.execute("CREATE INDEX idx_entries_user_source ON entries(user_id, source_type)")
    op.execute("CREATE INDEX idx_entries_metadata ON entries USING GIN(metadata)")

    op.execute(
        """
        CREATE TABLE context_sections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            section_type context_section_type NOT NULL DEFAULT 'custom',
            summary TEXT,
            body TEXT NOT NULL DEFAULT '',
            structured_facts JSONB NOT NULL DEFAULT '{}'::jsonb,
            confidence_level confidence_level NOT NULL DEFAULT 'low',
            confidence_notes TEXT,
            status context_status NOT NULL DEFAULT 'active',
            created_by context_revision_source NOT NULL DEFAULT 'user',
            updated_by context_revision_source NOT NULL DEFAULT 'user',
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            archived_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (user_id, title)
        )
        """
    )
    op.execute("CREATE INDEX idx_context_sections_user_status ON context_sections(user_id, status)")
    op.execute("CREATE INDEX idx_context_sections_user_type ON context_sections(user_id, section_type)")

    op.execute(
        """
        CREATE TABLE context_section_revisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            context_section_id UUID NOT NULL REFERENCES context_sections(id) ON DELETE CASCADE,
            revision_number INTEGER NOT NULL,
            title_snapshot TEXT NOT NULL,
            summary_snapshot TEXT,
            body_snapshot TEXT NOT NULL,
            structured_facts_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
            confidence_level_snapshot confidence_level NOT NULL,
            confidence_notes_snapshot TEXT,
            change_reason TEXT,
            changed_by context_revision_source NOT NULL,
            change_level ai_change_level NOT NULL DEFAULT 'report',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (context_section_id, revision_number)
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_context_section_revisions_section ON "
        "context_section_revisions(context_section_id, revision_number DESC)"
    )

    op.execute(
        """
        CREATE TABLE context_evidence_links (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            context_section_id UUID NOT NULL REFERENCES context_sections(id) ON DELETE CASCADE,
            context_section_revision_id UUID REFERENCES context_section_revisions(id) ON DELETE CASCADE,
            entry_id UUID NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
            relevance confidence_level NOT NULL DEFAULT 'medium',
            evidence_note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (context_section_id, entry_id, context_section_revision_id)
        )
        """
    )
    op.execute("CREATE INDEX idx_context_evidence_links_section ON context_evidence_links(context_section_id)")
    op.execute("CREATE INDEX idx_context_evidence_links_entry ON context_evidence_links(entry_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_context_evidence_links_entry")
    op.execute("DROP INDEX IF EXISTS idx_context_evidence_links_section")
    op.execute("DROP TABLE IF EXISTS context_evidence_links")
    op.execute("DROP INDEX IF EXISTS idx_context_section_revisions_section")
    op.execute("DROP TABLE IF EXISTS context_section_revisions")
    op.execute("DROP INDEX IF EXISTS idx_context_sections_user_type")
    op.execute("DROP INDEX IF EXISTS idx_context_sections_user_status")
    op.execute("DROP TABLE IF EXISTS context_sections")
    op.execute("DROP INDEX IF EXISTS idx_entries_metadata")
    op.execute("DROP INDEX IF EXISTS idx_entries_user_source")
    op.execute("DROP INDEX IF EXISTS idx_entries_user_created")
    op.execute("DROP TABLE IF EXISTS entries")

    op.execute("DROP TYPE IF EXISTS ai_change_level")
    op.execute("DROP TYPE IF EXISTS confidence_level")
    op.execute("DROP TYPE IF EXISTS context_revision_source")
    op.execute("DROP TYPE IF EXISTS context_status")
    op.execute("DROP TYPE IF EXISTS context_section_type")
    op.execute("DROP TYPE IF EXISTS entry_actor")
    op.execute("DROP TYPE IF EXISTS entry_source")
