# Test Strategy

## Goal

The app handles private personal planning state and AI-driven mutations. Tests need to protect against data leaks, broken planning transitions, and silent AI mistakes.

The test suite should be boring, practical, and close to the behavior users rely on.

## Backend Test Layers

### Unit Tests

Use for:

- planner selection logic
- capacity estimation
- review prompt filtering
- recurrence/date calculations
- AI intent-to-command conversion
- learned profile update calculations

### API Tests

Use for:

- endpoint success paths
- validation failures
- authentication failures
- user ownership boundaries
- archive behavior
- completion/partial/skip/move state transitions

### Database And Migration Tests

Use for:

- migration can upgrade from empty database
- uniqueness constraints
- foreign-key behavior
- routine instance idempotency
- archive instead of hard delete behavior

### AI Tests

AI calls should be mocked in normal tests.

Test:

- structured parser response handling
- malformed AI response handling
- clarification flow
- safe conversion of destructive suggestions into archive/no-op
- action log creation

Do not rely on live OpenAI calls for routine CI.

## Frontend Test Layers

### Component Tests

Use for:

- Today item states
- partial completion note dialog
- timeline/list toggle
- weekly planning review states
- daily review prompt rendering

### Integration Tests

Use for:

- API client behavior
- auth shell behavior
- form validation
- optimistic or loading states

### End-To-End Tests

Use for:

- login shell
- submit inbox item
- view generated Today
- complete a task
- partially complete a task
- submit daily review

## Critical Invariants

These should be tested repeatedly across the codebase:

- A user cannot read or mutate another user's data.
- AI never hard-deletes user planning data.
- Archived data does not appear in active default views.
- Partial completion preserves the raw user note.
- Replanning preserves completed, partial, skipped, fixed, and user-edited items.
- Routine instance generation is idempotent.
- Daily review does not prompt for every trivial missed item.
- OpenAI failures do not corrupt planning state.

## CI Expectations

Initial CI should run:

```bash
cd apps/api
uv run ruff check .
uv run pytest
```

Later CI should add:

- migration upgrade test against Postgres
- web lint/test
- web end-to-end smoke tests
- Android build/test once `apps/android` exists
