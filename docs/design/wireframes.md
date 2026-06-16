---
id: DESIGN-WIREFRAMES-001
title: Library Ops Wireframes and Design Handoff
status: accepted
source_of_truth: repo-local-design
related_prd: .taskmaster/docs/prd.md
---

# Library Ops Wireframes and Design Handoff

## Purpose

This file is the repo-local design source for the first implementation pass. It
keeps the UI implementable without private external design-tool access.

Use `docs/design/evaluator-design-handoff.md` for the durable evaluator-facing
screen/state matrix, role/action matrix, accessibility contract, and design token
fallback that must remain available without private design-tool access.
Use `docs/design/mockup-plan.md` for the low-fidelity mockup
execution plan and acceptance checks.

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

## Design authority rules

- Treat these repo-local wireframes as the design source of truth.
- Record any design change that affects behavior in the PRD or Task Master task.
- Do not require external design-tool access to implement the app.
