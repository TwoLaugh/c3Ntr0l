# Product HLD: AI Personal Operating System

## 1. Product Intent

This product is an AI-mediated personal operating system, not a conventional todo app.

Its purpose is to reduce the amount of life complexity the user has to hold in working memory. The user should be able to tell the system the mess, and the system should store the original material, understand what it means, organize what is actionable, and present only the next livable slice of the day.

Core promise:

> The system turns undigested life-input into inspectable understanding and realistic daily structure.

The product should feel calm, minimal, terse, intentional, non-corporate, non-gamified, and low-friction.

## 2. Target Scope

V1 is built primarily for one user, but the backend and data model should avoid dead ends for eventual productization.

V1 should support:

- Backend-hosted intelligence and storage.
- Separate web and Android frontends.
- Google login if implementation cost stays reasonable.
- A raw entry log for inbox messages, reviews, onboarding answers, and completion notes.
- AI-maintained context sections with evidence and version history.
- Visible categories for organizing and working through items.
- Items that cover tasks, routines, reminders, notes, milestones, and recurring actions.
- Today as the main execution surface.
- Timeline mode where AI suggests time blocks.
- List mode where AI orders work without explicit timings except fixed-time items.
- AI inbox that can update context, categories, items, and plans.
- Confirmation before disruptive in-day plan changes.
- Quick-start onboarding and multi-session deep onboarding.
- Daily and weekly reviews that feed entries and planning updates.
- AI activity log and context inspection screens tucked away from the main surface.

V1 should not attempt:

- Android launcher behavior.
- Calendar/weather/message integrations.
- Notification filtering.
- End-to-end encryption.
- Team/multi-tenant product features beyond basic `user_id` readiness.
- Advanced behavioral analytics from app usage and completion times.

## 3. Primary User Surfaces

### 3.1 Today

Today is the default home surface.

It contains the lived plan for the day:

- fixed commitments
- AI-suggested time blocks
- ordered list-mode items
- recurring item instances
- focus work
- maintenance work
- optional soft invitations
- buffer/recovery blocks

Timeline mode and list mode are different planning modes:

- Timeline mode lets the AI propose timings.
- List mode lets the AI order the day without assigning suggested times, except for fixed-time items.

### 3.2 Inbox Overlay

The inbox is how the user gives the system raw life material.

The everyday UI should be a floating bottom-right assistant button on Today. Opening it shows a compact overlay, not a full navigation detour.

The user can enter:

- tasks
- reminders
- worries
- observations
- routine changes
- category/project updates
- scheduling constraints
- review notes
- life context

The AI should store the original entry, decide which parts of the system are relevant, load targeted context, apply safe changes, and report tersely. It should ask questions only when ambiguity or practical scheduling issues matter.

### 3.3 Categories

Categories are visible organization buckets and work modes.

Examples:

- Driving test
- Back rehab
- House
- Work
- Diet app
- Home renovation
- Social
- Person: Will

Categories organize items. They are not the same as context sections. A category view should let the user say, in effect, "I am working on this now" and then work through the relevant item list.

### 3.4 Context Sections

Context sections are AI-maintained understanding documents.

They are generated from raw entries and are inspectable/editable by the user. They can be broad or specific:

- General life overview
- Health
- Capacity and energy
- Planning preferences
- Home renovation
- Person: Will
- Work situation

The AI should be able to inspect a lightweight index of section names and summaries, then load only relevant sections for a given operation.

Each context section should have:

- narrative summary
- structured facts or assumptions
- confidence/weight notes
- linked evidence entries
- revision history

### 3.5 Daily Review

Daily review is the adaptation surface.

It should be preloaded and task-aware. It should ask about missed or partially completed items only when the answer would meaningfully improve future planning.

It should avoid nagging about low-stakes missed items.

Daily review produces raw entries and may update:

- item status
- future plans
- context sections
- simple learned capability notes

### 3.6 Weekly Planning Review

Weekly review is the rhythm surface.

The system should generate weekly plans from:

- active items
- recurrence rules
- context sections
- recent reviews
- learned capability notes
- current priorities

The user can inspect, accept, and regenerate parts of the week. The system should not require manual week construction.

### 3.7 Deeper Admin Screens

Manual editing exists, but is not front-page behavior.

The user can inspect and edit:

- categories
- items
- context sections
- context revisions and evidence
- onboarding sessions
- profile assumptions
- planning preferences
- AI activity
- archived items

## 4. Core Concepts

### 4.1 Entries

Entries are raw source material.

Examples:

- inbox messages
- onboarding answers
- daily review responses
- weekly review responses
- completion notes

Entries are never deleted by default. They are the evidence layer from which context is distilled.

### 4.2 Context Sections

Context sections are generated understanding.

They are separate from categories. They can describe a topic, person, life area, constraint, preference, or pattern. V1 includes versioning and lightweight evidence/confidence so the AI's understanding is not a black box.

### 4.3 Categories

Categories are visible organizational buckets.

An item has one primary category by default. Items may also link to additional categories or context sections when cross-cutting relevance matters.

### 4.4 Items

Items are actionable or trackable units.

An item can be:

- action
- reminder
- routine
- recurring action
- milestone
- note

Items can have flags such as recurring, soft, fixed-time, important, energy-sensitive, social, health, or admin.

### 4.5 Plans And Plan Instances

Plans are generated structures for days and weeks.

Plan instances are the actual appearances of items in Today or a weekly plan. This keeps a durable recurring item, such as "Back rehab", separate from today's planned occurrence.

## 5. AI Behavior

AI changes happen automatically by default for low-risk updates.

The AI can:

- store entries
- create or update context sections
- create categories
- create or update items
- attach items to categories and context
- generate plan instances
- propose in-day plan changes
- update simple learned capability notes

The AI should not hard-delete data by default. User-created or AI-created items that were wrong should be archived with an audit reason.

AI change policy:

- Auto-apply: storing entries, category filing, backlog item creation, context distillation, low-risk metadata updates.
- Report: created/updated items, changed context sections, created categories.
- Confirm first: in-day schedule changes, major context rewrites, archiving important items, completion of user-important items, destructive privacy actions.

All meaningful AI actions should be logged quietly. The activity log is available if the user looks for it. A user setting can make AI changes more visible.

Default AI tone should be terse assistant tone. Tone should be configurable.

## 6. Planning Rhythm

Primary rhythm:

- Onboarding seeds entries, context sections, categories, and items.
- Sunday: generate weekly plan automatically.
- Each day: daily plan is derived from weekly plan, items, recurrences, inbox updates, context, and capability notes.
- During the day: inbox messages can add backlog items or propose plan changes.
- End of day: daily review creates entries and updates planning state.

Missed work behavior:

- Low-stakes skipped items can return quietly to backlog or be ignored based on type.
- Important missed items should be surfaced in review.
- The AI decides whether to move, defer, split, soften, or keep an item active based on review context.

## 7. V2 Learning Boundary

V1 should preserve evidence and create simple confidence notes.

V2 can improve:

- completion-time analytics
- behavioral pattern detection
- advanced evidence weighting
- adaptive capacity models
- richer usage-based learning

## 8. Product Principles

- Hide complexity until requested.
- Store original input before interpreting it.
- Make AI understanding inspectable and versioned.
- Keep categories practical and visible.
- Keep context nuanced and separate from categories.
- Prefer adaptive rhythm over productivity optimization.
- Treat partial completion as useful signal.
- Treat missed items as planning evidence, not moral failure.
- Keep AI autonomous but interruptible for disruptive changes.
