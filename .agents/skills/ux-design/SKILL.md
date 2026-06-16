---
name: ux-design
description: Use when designing wireframes, Figma MCP handoff, accessibility annotations, role-aware navigation, or UI flow design.
---

# UX Design Skill

## Triggers

Use this skill when work involves:

- a new screen or major UI flow;
- Figma MCP design generation or extraction;
- wireframe updates;
- accessibility annotations;
- empty/error/loading states;
- role-aware navigation;
- demo-script screenshots or evaluator-facing UX polish.

## Rules

- Treat `docs/design/wireframes.md` as the repo-local design source of truth.
- Figma MCP is required for design-generation and design-extraction tasks in implementation environments. Persist implementation decisions back to repo docs so coding tasks do not depend on private Figma access.
- Every major screen must specify: purpose, users, entry points, primary actions, empty state, error state, accessibility notes, and tests.
- Role permissions must be visible in the UI but enforced server-side.
- Prefer simple Django template + HTMX interactions over a custom client application.
- Use the installed `$screenshot`, `$playwright`, or `$playwright-interactive`
  skills alongside this one when visual QA or live browser evidence is part of
  the design task.

## Figma MCP workflow

When Figma MCP is available:

1. Start from the relevant PRD capability and Markdown wireframe.
2. Create or update frames for desktop-first evaluator flow.
3. Export only implementation-relevant decisions back into repo docs.
4. Do not store private Figma tokens, URLs, or auth material in the repo.

Suggested prompt shape:

```text
Create a clean desktop-first mockup for Library Ops screen <screen-name>.
Use Django/HTMX implementation constraints, accessible form states, role-aware actions,
and a pragmatic interview-demo aesthetic. Include empty/error/loading states.
```

## Output

- Screens affected:
- User journey:
- Component notes:
- HTMX interaction notes:
- Accessibility notes:
- Tests required:
- PRD/Task Master impact:
- Figma prompt:
