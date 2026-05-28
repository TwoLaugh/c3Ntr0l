# V2 HLD: Integrations And Attention Layer

## 1. Purpose

V2 extends the backend's planning intelligence with external context and begins moving toward the attention-layer vision.

V2 should remain guided by the same philosophy:

> Reduce cognitive fragmentation without turning the product into a controlling productivity machine.

## 2. Calendar Integration

Calendar integration gives the planner real availability.

Capabilities:

- read events
- identify fixed commitments
- infer available windows
- avoid scheduling over appointments
- warn about overloaded days
- include travel/prep buffers later

The calendar should feed the planner, not become the main UI.

## 3. Weather Integration

Weather helps planning for outdoor, travel, exercise, and house tasks.

Capabilities:

- check daily forecast
- avoid outdoor tasks during poor weather
- suggest weather-sensitive windows
- explain scheduling choices

Example:

```txt
Moved pressure washing to Saturday morning because Sunday looks wet.
```

## 4. Message And Email Awareness

This is potentially valuable but more complex and privacy-sensitive.

Possible capabilities:

- inspect selected inboxes or message sources
- identify genuinely important messages
- create tasks/reminders from messages
- suppress or summarize low-value noise
- surface urgent human communications

This likely requires careful user consent, source-by-source permissions, and very conservative defaults.

For email, Gmail integration is more feasible than SMS/WhatsApp/iMessage-style filtering.

For Android device messages, complexity depends heavily on platform APIs, notification access, accessibility permissions, and app policies.

## 5. Notification Layer

V2 may add reminders, but the product should not become notification-heavy.

Capabilities:

- remind for fixed commitments
- nudge for important blocks
- prompt daily review
- surface urgent external messages

Non-goal:

- constant habit nudging
- anxiety-driven alerts

## 6. Android Attention Layer

This is the bridge toward the launcher vision.

Possible features:

- minimalist Today-first home experience
- app opening through intent prompts
- purpose logging before opening distracting apps
- timers for intentional use
- grayscale/minimal modes if feasible
- app list hiding or simplification

This should be treated as its own design and technical project after V1 proves the planning system.

## 7. Android Launcher Direction

Launcher concept:

- Today is the home surface.
- Inbox is always available.
- Only a few intentional apps are surfaced.
- Distracting apps are opened through search/intent.

Example:

```txt
User: Open Chrome to research patio cleaners.
System: Opens Chrome, logs purpose, optionally starts a timer.
```

This is not strict lockdown. It is friction against automatic drift.

## 8. Analytics And Adaptation

V2 can add more meaningful analytics:

- routine adherence trends
- domain neglect signals
- planning accuracy
- overcommitment patterns
- time-of-day reliability
- partial completion patterns

Analytics should mostly serve the AI planner, not become a dashboard the user has to manage.

## 9. Integration Architecture

Add integration services behind the backend:

```txt
Calendar Provider
Weather Provider
Email Provider
Notification Provider
Android Device Context Provider
```

These providers should produce normalized planning context rather than leaking provider-specific complexity into planner logic.

Example normalized context:

```txt
ExternalContext
- fixed_commitments
- weather_constraints
- urgent_messages
- suggested_tasks
- unavailable_windows
```

## 10. V2 Risks

- privacy concerns
- platform restrictions
- notification fatigue
- AI overreach
- integrations making the product feel busy

The solution is to keep external context mostly invisible unless it changes the plan in a useful way.
