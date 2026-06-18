---
id: DESIGN-WIREFRAMES-001
title: Library Ops Wireframes and Design Handoff
status: accepted
source_of_truth: repo-local-design
related_prd: .taskmaster/docs/prd.md
---

# Library Ops Wireframes and Design Handoff

## Purpose

This file is the canonical repo-local design source for the first implementation
pass. It keeps the UI implementable without private external design-tool access
and absorbs the evaluator handoff and mockup-plan notes so the maintained
design surface stays in one place.

The design target is a polished but restrained engineering-manager interview
demo: clear workflows, visible quality gates, role-aware actions, accessible
forms, and no unnecessary visual complexity.

## Design principles

1. **Evaluator-first navigation.** A reviewer should verify the assignment in
   minutes: catalog, add/edit/archive, borrow/return, search, roles, seed data,
   and tests.
2. **Role clarity.** Admin, Librarian, Member, and anonymous users should see
   different affordances, but server-side authorization remains authoritative.
3. **Search confidence.** Results should explain whether they matched exact IDs,
   keyword/full-text, semantic similarity, or fused ranking.
4. **HTMX pragmatism.** Interactions should be server-rendered and enhanced with
   HTMX where it reduces page reload friction.
5. **Accessible defaults.** Keyboard navigation, focus order, error text,
   labels, and empty states must be specified before implementation.

## Visual system notes

- Layout: desktop-first responsive shell, max-width content, left navigation on
  authenticated pages, top bar on public pages.
- Typography: system font stack.
- Components: cards, tables, badges, search field, filters, modal/dialog,
  confirmation panel, toast/alert region.
- Color usage: keep semantic states obvious: available, on-loan, overdue,
  archived, destructive action. Define exact colors during implementation or in
  external design tools; do not hard-code design tokens here.
- Tone: clear, operational, not whimsical.

## Screen map

| Screen | Route | Primary users | Purpose |
|---|---|---|---|
| Public landing | `/` | Evaluator, anonymous | Explain demo and route to catalog/login. |
| Login | `/accounts/login/` | All | Sign in with demo credentials or OAuth. |
| Dashboard | `/dashboard/` | Admin, Librarian | Operational metrics and quick actions. |
| Catalog search | `/catalog/` | All | Search, filter, inspect availability. |
| Book detail | `/catalog/<edition-id>/` | All | Metadata, copies, actions, loans. |
| Book create/edit | `/catalog/new/`, `/catalog/<id>/edit/` | Admin, Librarian | Manage metadata and copies. |
| Checkout | HTMX modal/panel | Admin, Librarian | Borrow an available copy to a member. |
| Return | HTMX modal/panel | Admin, Librarian | Close an active loan. |
| Loans | `/loans/` | Admin, Librarian, Member | View active/historical loans. |
| Admin users | `/admin/users/` or Django Admin | Admin | Manage roles/users. |
| API/docs | `/api/docs` or Django Ninja OpenAPI route | All | Verify the public API contract and protected mutations. |
| AI metadata assist | HTMX panel | Admin, Librarian | Review suggested tags/description. |

## 1. Public landing

```text
+---------------------------------------------------------------+
| Library Ops                                  Catalog  Login |
+---------------------------------------------------------------+
| Mini Library Management System                                |
| A deployed, tested Django demo for catalog, circulation,       |
| search, RBAC, seed data, and grounded AI assistance.           |
|                                                               |
| [Browse catalog] [Sign in as demo user]                       |
|                                                               |
| Assignment checklist                                          |
| [x] Book management      [x] Borrow/return                    |
| [x] Search               [x] README + deployment              |
| [x] Auth/RBAC            [x] AI/search extras                 |
+---------------------------------------------------------------+
```

Implementation notes:

- Anonymous catalog access is allowed.
- The page should link to README evidence after deployment.
- Keep claims synchronized with actual implemented features.

Accessibility notes:

- Primary CTA first in tab order.
- Checklist must be text, not only icons.

## 2. Login

```text
+---------------------------------------------------------------+
| Library Ops                                                 |
+--------------------------+------------------------------------+
| Sign in                  | Demo accounts                      |
| Email [______________]   | Admin: admin@libraryops.demo       |
| Pass  [______________]   | Librarian: librarian@...           |
| [Sign in]                | Member: member@...                 |
|                          | Password: <local-demo-password-from-seed-command>      |
| [Continue with Google]   |                                    |
+--------------------------+------------------------------------+
```

Implementation notes:

- Demo credentials are disposable and recreated by seed command.
- OAuth may be configured but password login should keep the demo reliable.

Accessibility notes:

- Use explicit labels and error summaries.
- Do not place credentials only inside temporary text.

## 3. Dashboard

```text
+-------------+-------------------------------------------------+
| Nav         | Dashboard                                       |
| Dashboard   | +---------+ +---------+ +---------+ +---------+ |
| Catalog     | | Works   | | Copies  | | Active  | | Overdue | |
| Loans       | | 1,000   | | 1,280   | | 14      | | 2       | |
| Admin       | +---------+ +---------+ +---------+ +---------+ |
|             |                                                 |
|             | Quick actions                                   |
|             | [Add book] [Import corpus] [Build search index] |
|             |                                                 |
|             | Recent activity                                 |
|             | - Librarian checked out Copy B-00012            |
|             | - Import completed: 1,000 editions              |
+-------------+-------------------------------------------------+
```

Implementation notes:

- Admin/Librarian see operational actions.
- Member dashboard should show own loans instead of system metrics.

Accessibility notes:

- Metrics need labels readable by screen readers.
- Recent activity should be a semantic list.

## 4. Catalog search

```text
+-------------+-------------------------------------------------+
| Nav         | Catalog                                         |
|             | [ Search title, author, ISBN, subject...      ] |
|             | [Search] [Semantic: on/off]                    |
|             |                                                 |
|             | Filters                                         |
|             | Availability [Any v]  Subject [Any v]          |
|             | Language [Any v]      Source [Any v]           |
|             |                                                 |
|             | Results                                         |
|             | +---------------------------------------------+ |
|             | | Pride and Prejudice                         | |
|             | | Jane Austen · 1813 · English                | |
|             | | Available: 3 of 4 copies                    | |
|             | | Match: exact title + contributor            | |
|             | | [Details] [Checkout copy]                   | |
|             | +---------------------------------------------+ |
+-------------+-------------------------------------------------+
```

Implementation notes:

- Exact ISBN/barcode results should short-circuit or rank first.
- Result rows include match explanation from search service.
- Role-aware actions: anonymous/member see details; librarian/admin see checkout.
- HTMX can update result list and filters without full reload.

Accessibility notes:

- Search input has visible label.
- Filters are form controls with labels.
- Results count updates should use an ARIA live region.

Empty state:

```text
No matching books found.
Try a title, author, ISBN, or broader subject term.
```

## 5. Book detail

```text
+-------------+-------------------------------------------------+
| Nav         | Pride and Prejudice                             |
|             | Jane Austen                                     |
|             | [Cover]  ISBN: 978...  Source: Open Library     |
|             |         Subjects: Fiction, Classics, Society    |
|             |         Description...                          |
|             |                                                 |
|             | Copies                                          |
|             | Barcode     Status      Location    Action      |
|             | B-000001    Available   A1          [Checkout]  |
|             | B-000002    On loan     A1          [Return]    |
|             |                                                 |
|             | [Edit metadata] [Upload cover] [Archive]        |
+-------------+-------------------------------------------------+
```

Implementation notes:

- Metadata and live availability are separate sections.
- Archive action requires confirmation.
- Upload cover is Admin/Librarian only.

Accessibility notes:

- Destructive action confirmation must be keyboard accessible.
- Copy status badges must include text labels.

## 6. Create/edit book

```text
+---------------------------------------------------------------+
| Add book                                                      |
| Title *        [_________________________________________]     |
| Subtitle       [_________________________________________]     |
| Contributors * [Jane Austen                         + Add]     |
| ISBN-13        [_________________________________________]     |
| Publisher      [_________________________________________]     |
| Year           [____]  Language [English v]                   |
| Subjects       [Classics] [Fiction] [+]                       |
| Description    [_________________________________________]     |
| Cover URL      [_________________________________________]     |
| Upload cover   [Choose file]                                  |
| Initial copies [ 1 ]                                          |
|                                                               |
| [Save book] [Save and add another] [Cancel]                   |
|                                                               |
| AI assist: [Suggest tags and description]                     |
+---------------------------------------------------------------+
```

Implementation notes:

- Validation lives in forms and services.
- AI suggestions open in a review panel and are not auto-saved.
- Initial copies generate deterministic barcodes or require explicit barcode.

Accessibility notes:

- Required fields must be indicated in text.
- Form errors must render near the field and in an error summary.

## 7. Checkout modal/panel

```text
+---------------------------------------------------------------+
| Checkout copy B-000001                                       |
| Book: Pride and Prejudice                                    |
| Status: Available                                            |
| Patron * [Search/select member___________________________]    |
| Due date [2026-07-03]                                        |
|                                                               |
| [Checkout] [Cancel]                                          |
+---------------------------------------------------------------+
```

Implementation notes:

- Service must run transactionally.
- Duplicate active-loan constraint is authoritative.
- On success, HTMX refreshes copy table and dashboard metric.

Accessibility notes:

- Focus moves into modal and returns to initiating button.
- Errors must explain if copy became unavailable.

## 8. Return modal/panel

```text
+---------------------------------------------------------------+
| Return copy B-000002                                         |
| Borrowed by: Member Demo                                     |
| Checked out: 2026-06-12                                      |
| Due: 2026-07-03                                              |
|                                                               |
| [Return copy] [Cancel]                                       |
+---------------------------------------------------------------+
```

Implementation notes:

- Return closes active loan and sets copy available in one transaction.
- Historical loan remains visible.

## 9. Loans

```text
+-------------+-------------------------------------------------+
| Nav         | Loans                                           |
|             | [Active] [Overdue] [Returned] [Mine]            |
|             |                                                 |
|             | Book                Patron       Due      Action |
|             | Pride and...        Member Demo  Jul 03   Return |
|             | Frankenstein        Member Demo  Jun 10   Return |
+-------------+-------------------------------------------------+
```

Implementation notes:

- Member sees only own loans.
- Librarian/Admin see all loans.

## 10. AI metadata assist

```text
+---------------------------------------------------------------+
| AI suggestions                                                |
| Source fields: title, contributor, description                |
|                                                               |
| Suggested subjects: [Classic] [Social class] [Marriage]       |
| Suggested summary: ...                                        |
| Confidence / notes: grounded in provided fields only          |
|                                                               |
| [Apply selected] [Dismiss]                                    |
+---------------------------------------------------------------+
```

Implementation notes:

- Suggestions are structured output and human-reviewed.
- Persist provenance if suggestions are applied.
- Do not generate availability or copy state.

## 11. API/docs evaluator link

```text
+---------------------------------------------------------------+
| API docs                                                      |
| OpenAPI schema  /api/openapi.json                              |
| [Open docs] [Back to dashboard] [Back to catalog]             |
|                                                               |
| Demo access: Admin, Librarian, Member labels only              |
| Protected mutations require auth and role checks               |
+---------------------------------------------------------------+
```

Implementation notes:

- Surface the OpenAPI UI or JSON route selected during implementation.
- Keep the docs page visible to anonymous users, but block protected mutation
  execution.
- Link back to the dashboard, catalog, and README evidence.

States:

| State | Requirement |
|---|---|
| Default | OpenAPI UI loads and includes catalog, loans, and auth-related endpoints. |
| Unauthenticated | Read docs remain visible; protected endpoint execution is blocked by auth. |
| Permission denied | Error copy names the required role without exposing internals. |
| Schema error | Show a concise failure banner and link to setup/quality checks. |

## 12. Evaluator contract

### Role and action matrix

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

### State matrix

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

### Accessibility contract

- Initial focus lands on the page heading after navigation and on the dialog
  title after modal open.
- Dialogs use an accessible name, keep focus within the modal while open, close
  on Escape, and return focus to the trigger.
- Error summaries receive focus after failed submit and each field with an
  error uses `aria-describedby`.
- Search result updates and checkout/return success messages use an ARIA live
  region.
- Status badges include text, not color alone.
- Destructive actions require a keyboard-accessible confirmation.
- Tables retain headers on narrow screens or collapse into labeled rows.
- Playwright/a11y tests cover catalog search, create/edit validation, checkout
  conflict, return conflict, member loans, admin denial, and API docs loading.

### Design token fallback

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

## Implementation extraction checklist

When extracting wireframes or implementation notes into code, capture:

- route name;
- template name;
- context/viewmodel fields;
- form fields and validation errors;
- HTMX targets and swap behavior;
- permission conditions;
- empty/error/loading states;
- Playwright assertions.

When extracting the evaluator contract, also capture:

- API/docs route and auth behavior;
- role-specific admin and member states;
- evaluator link targets back to README and canonical docs;
- confirmation copy for protected admin mutations.

## Design authority rules

- Treat these repo-local wireframes as the design source of truth.
- Record any design change that affects behavior in the PRD or Task Master task.
- Do not require external design-tool access to implement the app.
