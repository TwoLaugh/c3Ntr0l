# Web Frontend HLD

## 1. Role

The web app is the full planning, review, inspection, and editing interface.

The everyday experience should still be quiet: Today first, inbox as an overlay, and deeper screens tucked behind a burger menu. The web app can support richer admin and inspection than Android, but should not feel like a database dashboard.

## 2. Recommended Stack

- Next.js
- TypeScript
- React Query or equivalent server-state library
- Lightweight CSS/design-token system
- Custom timeline/list UI for Today

Visual style should be dark, calm, low-stimulation, and utility-focused. Avoid decorative dashboard clutter.

## 3. App Shell

Primary shell:

- Today is the home screen.
- Secondary navigation lives in a burger menu.
- Bottom-right circular assistant button opens the inbox overlay.
- AI Activity and context inspection are available but not front-page behavior.

Burger menu destinations:

- Today
- Categories
- Items
- Context
- Reviews
- Onboarding
- Settings
- AI Activity
- Archive

## 4. Today Screen

Today is the default surface.

### 4.1 Timeline Mode

Timeline mode displays ordered time blocks:

- fixed blocks
- AI-suggested work blocks
- recurring item instances
- floating/flexible blocks
- buffer blocks

Each block should support:

- complete
- partial
- skip
- move
- edit
- open details

Suggested timings should feel light, not coercive. UI copy and styling should distinguish fixed commitments from AI suggestions.

### 4.2 List Mode

List mode is a different planning mode, not merely timeline with hidden text.

It shows ordered items and avoids explicit suggested times except for fixed-time items. It is for users who want structure without being time-boxed.

### 4.3 In-Day Plan Changes

If an inbox message affects today, the UI should show the AI proposal before applying it.

Examples:

- insert urgent item
- move a block
- defer a block
- regenerate the rest of today

The user can accept or reject the proposed change.

## 5. Inbox Overlay

The inbox should feel like summoning the assistant.

Primary UI:

- floating bottom-right button
- overlay/sheet with input
- terse response
- clarification question if needed
- proposed plan change if needed
- recent messages optionally visible but not cluttering the main surface

The full entry and action history can exist in deeper screens.

## 6. Categories

Categories are visible work buckets.

Category list should show:

- category name
- active item count
- next recommended item
- recently touched signal

Category detail should show:

- active items
- next recommended item with concise reason
- blockers
- relevant context snippets
- completion/partial/skip controls
- add item / send category-specific inbox note

The category view supports the mode: "I am working on this now."

## 7. Items

Item management replaces task/routine management.

Item editor should support:

- title
- notes
- primary category
- item type
- flags
- recurrence
- due date / do window
- effort and energy
- linked context sections
- status/history

The UI should expose enough control for correction without making manual maintenance the primary workflow.

## 8. Context

Context inspection is a trust surface.

Context list should show:

- section title
- section type
- updated date
- confidence/weight summary

Context detail should show:

- narrative summary
- structured facts/assumptions
- confidence notes
- evidence entries
- revision history
- AI/user source for revisions

The user can manually edit a context section. Manual edits create revisions.

## 9. Onboarding

Onboarding has two modes:

- Quick Start: enough to create the first useful Today.
- Deep Dive: a multi-session life interview that can be paused and resumed.

Deep Dive chapters:

- life overview
- health/body
- work/future
- home/admin
- people/social
- attention/friction/phone
- meaning/aliveness
- capacity/routines
- assistant preferences

Onboarding answers should be stored as entries and distilled into context, categories, and items.

## 10. Daily Review

Daily review should be short and preloaded.

It should show:

- important missed items
- partial completions needing notes
- energy/load check
- mood if useful
- open note box

It should avoid asking about every trivial skipped routine.

Review submissions create entries and can update context/items/plans.

## 11. Weekly Planning Review

Weekly review should show:

- week summary
- focus categories
- daily load
- overloaded days
- important deadlines
- recurring items
- deferred items
- proposed adjustments

User actions:

- accept week
- regenerate selected day
- adjust focus
- move items between days
- add constraints through inbox overlay

## 12. Settings

Settings should include:

- tone: terse assistant default, warmer alternatives
- default Today mode
- AI change visibility
- planning preferences
- profile assumptions
- auth/account

## 13. AI Activity

The AI activity log should show:

- what changed
- when
- why
- source entry/review/onboarding session
- undo option where available

This builds trust without cluttering the main experience.
