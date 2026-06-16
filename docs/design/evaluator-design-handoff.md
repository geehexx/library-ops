---
id: DESIGN-EVALUATOR-HANDOFF-001
title: Evaluator Design Handoff
status: accepted
source_of_truth: repo-local-design
related_prd: ../.taskmaster/docs/prd.md
---

# Evaluator Design Handoff

This companion to `docs/design/wireframes.md` records evaluator-visible UI
requirements that must not depend on private external design-tool state.

## Missing Product Surfaces

### API/docs evaluator link

Route: `/api/docs` or the Django Ninja OpenAPI route selected during
implementation.

Purpose: let an evaluator verify the API contract and protected endpoint
behavior without reading source first.

Visible elements:

- page title, API version, and OpenAPI schema link;
- links back to the dashboard, catalog, and README evidence;
- note that protected mutations require Admin or Librarian credentials;
- non-secret demo account labels, with password details only if the seed command
  intentionally documents disposable demo credentials.

States:

| State | Requirement |
|---|---|
| Default | OpenAPI UI loads and includes catalog, loans, and auth-related endpoints. |
| Unauthenticated | Read docs remain visible; protected endpoint execution is blocked by auth. |
| Permission denied | Error copy names the required role without exposing internals. |
| Schema error | Show a concise failure banner and link to setup/runbook checks. |

### Admin users and roles

Route: `/admin/users/` or Django Admin with a documented app-facing entry point.

Purpose: prove Admin-only role management and make role boundaries visible.

Visible elements:

- table of users with email, display name, role, active state, and last login;
- filter by role and active state;
- edit role action for Admin only;
- unavailable or hidden mutation controls for Librarian and Member;
- confirmation text before role changes.

States:

| State | Requirement |
|---|---|
| Empty | Explain how to run the seed roles/users command. |
| Validation error | Field-level role error and summary focus. |
| Permission denied | Non-admin users receive a clear denial page or alert. |
| Success | Toast or alert announces the changed user and role. |

### Member loans

Route: `/loans/mine/` or `/loans/` filtered by the current Member.

Purpose: show Members their own borrowing history without privileged circulation
actions.

Visible elements:

- active loans first, then returned history;
- book title, copy barcode, checkout date, due date, return date, and overdue
  state;
- no checkout, return, edit, or admin controls;
- link to catalog/book detail.

States:

| State | Requirement |
|---|---|
| Empty | "No current loans" plus a catalog link. |
| Overdue | Text label and semantic status styling. |
| Returned | Return date shown; action column omitted. |
| Anonymous | Redirect to login or show sign-in prompt. |

## Role And Action Matrix

| Surface/action | Anonymous | Member | Librarian | Admin |
|---|---:|---:|---:|---:|
| View landing and public catalog | Yes | Yes | Yes | Yes |
| View own loans | No | Yes | Yes, filtered by patron | Yes |
| View all loans | No | No | Yes | Yes |
| Create/edit/archive catalog record | No | No | Yes | Yes |
| Checkout/return copy | No | No | Yes | Yes |
| Run import/search-index actions | No | No | Yes, if enabled | Yes |
| Review/apply AI metadata suggestions | No | No | Yes | Yes |
| Manage users and roles | No | No | No | Yes |
| Open API docs | Yes | Yes | Yes | Yes |
| Execute protected API mutations | No | No | Yes | Yes |

UI affordances may hide unavailable actions, but server-side authorization and
API tests remain authoritative.

## State Matrix

| Surface | Loading | Empty | Error | Permission | Success |
|---|---|---|---|---|---|
| Dashboard | Skeleton metrics | Seed/setup callout | Metric load banner | Member variant | Recent activity update |
| Catalog | Search spinner | No matches text | Search unavailable | Hidden privileged actions | Result count live update |
| Book detail | Copy table spinner | No copies | Metadata load banner | Edit/archive hidden | Copy table refresh |
| Create/edit | Save button busy | Not applicable | Error summary | Denial page | Redirect/toast |
| Checkout | Patron search busy | No patron found | Copy unavailable | Action hidden | Modal closes and row refreshes |
| Return | Button busy | No active loan | Conflict text | Action hidden | Loan closed and row refreshes |
| Loans | Table spinner | No loans | Load banner | Member-only filter | Status update |
| Admin users | Table spinner | No users | Validation summary | Denial page | Role change toast |
| API/docs | OpenAPI loading | No schema | Schema load banner | Auth prompt | Endpoint response shown |

## Accessibility Contract

- Initial focus lands on the page heading after navigation and on the dialog
  title after modal open.
- Dialogs use an accessible name, keep focus within the modal while open, close
  on Escape, and return focus to the trigger.
- Error summaries receive focus after failed submit and each field with an error uses
  `aria-describedby`.
- Search result updates and checkout/return success messages use an ARIA live
  region.
- Status badges include text, not color alone.
- Destructive actions require a keyboard-accessible confirmation.
- Tables retain headers on narrow screens or collapse into labeled rows.
- Playwright/a11y tests cover catalog search, create/edit validation, checkout
  conflict, return conflict, member loans, admin denial, and API docs loading.

## Design Token Fallback

Externally-derived design tokens are advisory until mirrored here.

| Token | Value |
|---|---|
| Font | System UI stack |
| Page max width | 1200 px |
| Spacing | 4, 8, 12, 16, 24, 32 px |
| Radius | 4 px controls, 8 px repeated cards |
| Focus ring | 2 px solid, high contrast, outside offset |
| Available | Green text and badge with "Available" label |
| On loan | Blue or neutral badge with "On loan" label |
| Overdue | Red text/badge with "Overdue" label |
| Archived | Neutral badge with "Archived" label |
| Destructive | Red action text/button with confirmation |

Responsive behavior:

- desktop uses a left navigation shell for authenticated users;
- tablet keeps nav visible if width allows, otherwise collapses to top nav;
- mobile stacks filters before results and converts dense tables to labeled row
  groups;
- action bars wrap rather than overflowing.

## Design Handoff Rule

External design-tool access is operator-local. Additional visual exploration can
improve polish, but an
implementation-affecting decision is accepted only after it is reflected in
`docs/design/wireframes.md`, this file, the PRD, or a Task Master task note.
