# Product HLD: AI Personal Operating System

## 1. Product Intent

This product is an AI-mediated personal operating system, not a conventional todo app.

Its purpose is to reduce the amount of life complexity the user has to hold in working memory. The user should be able to tell the system the mess, and the system should organize it into tasks, routines, plans, reviews, and adaptive daily structure.

The product should feel calm, minimal, terse, intentional, non-corporate, non-gamified, and low-friction.

Core promise:

> The system turns undigested life-input into a realistic next slice of lived life.

## 2. Target Scope

V1 is built primarily for one user, but the data model and backend should be ready for eventual productization.

V1 should support:

- Backend-hosted intelligence and storage.
- Separate web and Android frontends.
- Google login if the implementation cost stays reasonable.
- AI inbox that automatically mutates the user's planning state.
- Task, routine, domain, and lightweight project management.
- Weekly planning generated automatically on Sundays.
- Weekly planning review screen.
- Daily schedule with timeline/time-block default.
- List view alternative that removes suggested timings.
- Task-aware daily review.
- Notes-based partial completion.
- User profile with declared onboarding data and learned capability data.
- Quiet AI activity log tucked away from the main surface.

V1 should not attempt:

- Android launcher behavior.
- Calendar/weather/message integrations.
- Notification filtering.
- End-to-end encryption.
- Team/multi-tenant product features beyond basic `user_id` readiness.
- Complex project management.

## 3. Primary User Surfaces

### 3.1 Today

The main execution surface.

Default mode is a timeline with ordered time blocks. The system should suggest timings, but those timings should feel adjustable rather than authoritarian.

Today includes:

- Fixed blocks.
- Suggested blocks.
- Routine instances.
- Focus tasks.
- Maintenance tasks.
- Buffer/recovery blocks.
- Optional or floating tasks.

Today also has a list mode. List mode hides suggested timings and lets the user operate from an ordered task list.

### 3.2 Inbox

The capture surface.

The user enters rough, natural language:

- tasks
- plans
- worries
- reminders
- routine changes
- domain/project updates
- scheduling constraints
- review notes

The inbox should not present a cluttered visible chat history by default. The backend stores message history and AI actions, but the main interface should feel like a clean command box with recent results or confirmations.

### 3.3 Weekly Planning Review

The weekly rhythm surface.

Every Sunday, the backend automatically generates the coming week's plan. The user can open a review screen to inspect and adjust:

- weekly focus areas
- major tasks
- routines
- domain balance
- fixed commitments
- overloaded days
- deferred items

The system should not require the user to build the week manually.

### 3.4 Daily Review

The adaptation surface.

Daily review should be preloaded and task-aware. It should ask about missed or partially completed items only when the answer would meaningfully improve planning.

It should avoid nagging about low-stakes missed items.

Review captures:

- completed work
- partial work
- missed important work
- energy/load
- mood if useful
- notes/explanations
- needed adjustments

### 3.5 Deeper Admin Screens

Manual editing exists, but it is not front-page behavior.

The user can inspect and edit:

- tasks
- projects
- domains
- routines
- user profile assumptions
- planning preferences
- AI activity log
- archived items

## 4. Core Concepts

### 4.1 Domains

Domains are broad life areas.

Examples:

- Foundations
- Health Repair
- Work / Future Building
- Infrastructure
- Human Participation
- Soul / Meaning

Domains help the planner balance long-term attention.

### 4.2 Projects

Projects are lightweight outcome containers inside domains.

Examples:

- Prepare for driving test
- Build personal OS app
- Fix back pain routine
- Improve house exterior

Projects should exist in V1, but remain simple. They group tasks and preserve context.

### 4.3 Tasks

Tasks are concrete units of action.

Tasks can be scheduled, deferred, archived, completed, partially completed, or skipped. Domain-specific details should be stored as flexible metadata rather than separate task tables.

### 4.4 Routines

Routines are recurring behaviors.

Routines generate task instances so that the system can track adherence, completion, partial completion, skips, and review context.

### 4.5 Plans

Plans are generated schedule structures.

Weekly plans provide broad structure. Daily plans provide executable blocks. Plans should be stored, not merely calculated live, so the user can edit them and the system can learn from them.

## 5. AI Behavior

AI changes happen automatically by default.

The AI can:

- create tasks
- edit tasks
- archive tasks
- create routines
- generate task instances
- assign domains/projects
- create or update plans
- adjust future planning based on reviews
- update learned user profile assumptions

The AI should not hard-delete tasks. Items created in error should be archived with an audit reason.

All AI actions should be logged quietly. The activity log is available if the user looks for it. A user setting can make AI changes more visible.

Default AI tone should be terse assistant tone. Tone should be configurable.

## 6. Planning Rhythm

Primary rhythm:

- Sunday: generate weekly plan automatically.
- User can open weekly planning review.
- Each day: daily plan is derived from weekly plan, routines, new inbox items, and user capability state.
- During the day: inbox messages can trigger replanning.
- End of day: daily review updates task state and planning assumptions.

Missed work behavior:

- Low-stakes skipped items can return quietly to backlog or be ignored based on type.
- Important missed items should be surfaced in review.
- The AI decides whether to move, defer, split, soften, or keep a task active based on review context.

## 7. Product Principles

- Hide complexity until requested.
- Store enough structure for intelligence, but display only what matters now.
- Prefer adaptive rhythm over productivity optimization.
- Treat partial completion as useful signal.
- Treat missed tasks as planning evidence, not moral failure.
- Keep AI autonomous but inspectable.
- Design V1 for personal use, but avoid architectural dead ends for productization.
