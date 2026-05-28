# Web Frontend HLD

## 1. Role

The web app is the full management and planning interface.

It should be desktop-first, while remaining usable on narrower screens. The Android app is the main mobile execution surface, so the web app can prioritize comfortable planning, review, and deeper editing.

## 2. Recommended Stack

- Next.js
- TypeScript
- Tailwind CSS or a similarly lightweight styling system
- React Query or equivalent server-state library
- Calendar/timeline component built custom enough to match the product tone

Visual style should be quiet, sparse, and utility-focused.

## 3. Main Navigation

Primary destinations:

- Today
- Inbox
- Weekly Review
- Domains
- Projects
- Routines
- Archive
- Settings
- AI Activity

Today and Inbox should be the fastest to reach.

AI Activity, Archive, and deep editing screens should exist but stay out of the user's face.

## 4. Today Screen

Today is the default home screen.

### 4.1 Timeline Mode

Default mode.

Displays ordered time blocks:

- fixed blocks
- suggested work blocks
- routine instances
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

Alternative mode.

List mode hides suggested timings and shows ordered items. It uses the same `DailyPlanItem` data but renders by position/status rather than time.

List mode is for users who want structure without being time-boxed.

### 4.3 Plan Adjustment

The user should be able to:

- regenerate today's plan
- move a block
- mark a block as too much today
- add a note
- send a change through inbox

The system should preserve user edits during replanning where practical.

## 5. Inbox Screen

The inbox is a command surface, not a visible chat room.

Primary UI:

- large text input
- submit action
- terse result message
- recent applied changes optionally shown

The full message/action history can exist in a deeper view.

Example result:

```txt
Added "pressure wash paths" to house maintenance and placed it in Saturday morning's plan.
```

If clarification is required, the UI should show a concise question.

## 6. Weekly Planning Review

Opened after the Sunday plan is generated or manually from navigation.

Should show:

- week summary
- major focus areas
- day-by-day time load
- overloaded days
- important deadlines
- recurring routines
- deferred items
- domain balance

User actions:

- accept week
- adjust focus
- regenerate selected day
- move tasks between days
- open item details
- add constraints through inbox

## 7. Daily Review

Review screen is generated from the current day's plan and events.

It should be short.

Sections:

- completed summary
- important missed items
- partial items needing notes
- energy/load check
- open note box

It should not ask about every missed trivial routine.

## 8. Domains And Projects

Domain screens should be lightweight maps of life areas.

Domain view:

- active projects
- active tasks
- routines
- neglected signals
- recent completions

Project view:

- desired outcome
- next actions
- backlog
- notes
- recent history

Avoid making this feel like enterprise project management.

## 9. Routines

Routine management should allow:

- recurrence setup
- preferred time window
- active/inactive status
- effort estimate
- generated history

Routines should feel like living rhythms, not habit streaks.

## 10. Settings

Settings should include:

- tone: terse assistant default, warmer alternatives
- default Today view
- AI change visibility
- planning preferences
- profile assumptions
- auth/account

## 11. AI Activity

The AI activity log is a deeper screen.

It should show:

- what changed
- when
- why
- source
- undo option where available

This builds trust without cluttering the main experience.
