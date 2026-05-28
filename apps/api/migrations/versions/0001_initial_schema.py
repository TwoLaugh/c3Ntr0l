"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-28
"""

from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.execute("CREATE TYPE task_status AS ENUM ('active', 'completed', 'archived')")
    op.execute("CREATE TYPE task_priority AS ENUM ('low', 'normal', 'high', 'urgent')")
    op.execute("CREATE TYPE energy_level AS ENUM ('low', 'medium', 'high')")
    op.execute("CREATE TYPE plan_status AS ENUM ('draft', 'active', 'accepted', 'superseded', 'archived')")
    op.execute(
        "CREATE TYPE plan_item_status AS ENUM "
        "('planned', 'in_progress', 'completed', 'partial', 'skipped', 'moved', 'archived')"
    )
    op.execute("CREATE TYPE plan_block_type AS ENUM ('fixed', 'suggested', 'routine', 'floating', 'buffer')")
    op.execute("CREATE TYPE completion_event_type AS ENUM ('complete', 'partial', 'skipped', 'moved', 'abandoned')")
    op.execute("CREATE TYPE source_type AS ENUM ('user', 'ai', 'routine_engine', 'review', 'scheduler', 'integration')")

    op.execute(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT NOT NULL UNIQUE,
            display_name TEXT,
            auth_provider TEXT NOT NULL DEFAULT 'google',
            auth_subject TEXT UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE user_profiles (
            user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            timezone TEXT NOT NULL DEFAULT 'Europe/London',
            default_tone TEXT NOT NULL DEFAULT 'terse',
            preferred_day_view TEXT NOT NULL DEFAULT 'timeline',
            wake_time TIME,
            sleep_time TIME,
            work_hours JSONB NOT NULL DEFAULT '{}'::jsonb,
            planning_style TEXT,
            review_style TEXT,
            ai_change_visibility TEXT NOT NULL DEFAULT 'quiet',
            onboarding_completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE learned_capability_profiles (
            user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            weekday_focus_minutes_typical INTEGER,
            weekend_focus_minutes_typical INTEGER,
            weekday_maintenance_minutes_typical INTEGER,
            weekend_maintenance_minutes_typical INTEGER,
            morning_reliability NUMERIC(4,3),
            afternoon_reliability NUMERIC(4,3),
            evening_reliability NUMERIC(4,3),
            plan_completion_rate_14d NUMERIC(4,3),
            plan_completion_rate_30d NUMERIC(4,3),
            routine_completion_rate_14d NUMERIC(4,3),
            overload_sensitivity NUMERIC(4,3),
            confidence_score NUMERIC(4,3) NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE domains (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            weight NUMERIC(5,2) NOT NULL DEFAULT 1,
            active BOOLEAN NOT NULL DEFAULT true,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (user_id, name)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE projects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            domain_id UUID REFERENCES domains(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            desired_outcome TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            deadline TIMESTAMPTZ,
            notes TEXT,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            archived_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE inbox_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            raw_text TEXT NOT NULL,
            processing_status TEXT NOT NULL DEFAULT 'pending',
            parsed_intents JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            processed_at TIMESTAMPTZ
        )
        """
    )

    op.execute(
        """
        CREATE TABLE tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            domain_id UUID REFERENCES domains(id) ON DELETE SET NULL,
            project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
            source_inbox_message_id UUID REFERENCES inbox_messages(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            notes TEXT,
            status task_status NOT NULL DEFAULT 'active',
            priority task_priority NOT NULL DEFAULT 'normal',
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

    op.execute("CREATE INDEX idx_tasks_user_status ON tasks(user_id, status)")
    op.execute("CREATE INDEX idx_tasks_user_due_at ON tasks(user_id, due_at)")
    op.execute("CREATE INDEX idx_tasks_user_do_window ON tasks(user_id, do_window_start, do_window_end)")
    op.execute("CREATE INDEX idx_tasks_user_domain ON tasks(user_id, domain_id)")
    op.execute("CREATE INDEX idx_tasks_user_project ON tasks(user_id, project_id)")

    op.execute(
        """
        CREATE TABLE routines (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            domain_id UUID REFERENCES domains(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            notes TEXT,
            recurrence_rule TEXT NOT NULL,
            preferred_time_window JSONB NOT NULL DEFAULT '{}'::jsonb,
            effort_estimate_minutes INTEGER,
            energy_required energy_level,
            active BOOLEAN NOT NULL DEFAULT true,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            archived_at TIMESTAMPTZ
        )
        """
    )

    op.execute(
        """
        CREATE TABLE routine_instances (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            routine_id UUID NOT NULL REFERENCES routines(id) ON DELETE CASCADE,
            task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            scheduled_for_date DATE NOT NULL,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (routine_id, scheduled_for_date)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE weekly_plans (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            week_start_date DATE NOT NULL,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            summary TEXT,
            focus_notes TEXT,
            capacity_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
            status plan_status NOT NULL DEFAULT 'draft',
            accepted_at TIMESTAMPTZ,
            UNIQUE (user_id, week_start_date)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE daily_plans (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            weekly_plan_id UUID REFERENCES weekly_plans(id) ON DELETE SET NULL,
            plan_date DATE NOT NULL,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            default_view_mode TEXT NOT NULL DEFAULT 'timeline',
            capacity_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
            summary TEXT,
            status plan_status NOT NULL DEFAULT 'draft',
            UNIQUE (user_id, plan_date)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE daily_plan_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            daily_plan_id UUID NOT NULL REFERENCES daily_plans(id) ON DELETE CASCADE,
            task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
            title_snapshot TEXT NOT NULL,
            suggested_start TIMESTAMPTZ,
            suggested_end TIMESTAMPTZ,
            do_window_start TIMESTAMPTZ,
            do_window_end TIMESTAMPTZ,
            block_type plan_block_type NOT NULL DEFAULT 'suggested',
            position INTEGER NOT NULL,
            is_fixed_time BOOLEAN NOT NULL DEFAULT false,
            is_optional BOOLEAN NOT NULL DEFAULT false,
            reason_selected TEXT,
            status plan_item_status NOT NULL DEFAULT 'planned',
            user_edited_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX idx_daily_plan_items_plan_position ON daily_plan_items(daily_plan_id, position)")
    op.execute("CREATE INDEX idx_daily_plan_items_user_task ON daily_plan_items(user_id, task_id)")

    op.execute(
        """
        CREATE TABLE task_completion_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            plan_item_id UUID REFERENCES daily_plan_items(id) ON DELETE SET NULL,
            event_type completion_event_type NOT NULL,
            note TEXT,
            ai_interpretation JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE daily_reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            review_date DATE NOT NULL,
            prompts JSONB NOT NULL DEFAULT '[]'::jsonb,
            responses JSONB NOT NULL DEFAULT '{}'::jsonb,
            energy_level energy_level,
            load_fit TEXT,
            mood TEXT,
            ai_summary TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (user_id, review_date)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE ai_action_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_type source_type NOT NULL,
            source_id UUID,
            action_type TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id UUID,
            before_state JSONB,
            after_state JSONB,
            reason TEXT,
            reversible BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX idx_ai_action_logs_user_created ON ai_action_logs(user_id, created_at DESC)")
    op.execute("CREATE INDEX idx_ai_action_logs_target ON ai_action_logs(target_type, target_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ai_action_logs_target")
    op.execute("DROP INDEX IF EXISTS idx_ai_action_logs_user_created")
    op.execute("DROP TABLE IF EXISTS ai_action_logs")
    op.execute("DROP TABLE IF EXISTS daily_reviews")
    op.execute("DROP TABLE IF EXISTS task_completion_events")
    op.execute("DROP INDEX IF EXISTS idx_daily_plan_items_user_task")
    op.execute("DROP INDEX IF EXISTS idx_daily_plan_items_plan_position")
    op.execute("DROP TABLE IF EXISTS daily_plan_items")
    op.execute("DROP TABLE IF EXISTS daily_plans")
    op.execute("DROP TABLE IF EXISTS weekly_plans")
    op.execute("DROP TABLE IF EXISTS routine_instances")
    op.execute("DROP TABLE IF EXISTS routines")
    op.execute("DROP INDEX IF EXISTS idx_tasks_user_project")
    op.execute("DROP INDEX IF EXISTS idx_tasks_user_domain")
    op.execute("DROP INDEX IF EXISTS idx_tasks_user_do_window")
    op.execute("DROP INDEX IF EXISTS idx_tasks_user_due_at")
    op.execute("DROP INDEX IF EXISTS idx_tasks_user_status")
    op.execute("DROP TABLE IF EXISTS tasks")
    op.execute("DROP TABLE IF EXISTS inbox_messages")
    op.execute("DROP TABLE IF EXISTS projects")
    op.execute("DROP TABLE IF EXISTS domains")
    op.execute("DROP TABLE IF EXISTS learned_capability_profiles")
    op.execute("DROP TABLE IF EXISTS user_profiles")
    op.execute("DROP TABLE IF EXISTS users")

    op.execute("DROP TYPE IF EXISTS source_type")
    op.execute("DROP TYPE IF EXISTS completion_event_type")
    op.execute("DROP TYPE IF EXISTS plan_block_type")
    op.execute("DROP TYPE IF EXISTS plan_item_status")
    op.execute("DROP TYPE IF EXISTS plan_status")
    op.execute("DROP TYPE IF EXISTS energy_level")
    op.execute("DROP TYPE IF EXISTS task_priority")
    op.execute("DROP TYPE IF EXISTS task_status")
