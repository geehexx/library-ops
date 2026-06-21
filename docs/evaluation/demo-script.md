# Release demo script

Use this as the evaluator-facing talk track for the release bundle. Keep the
demo to one pass, about 3-6 minutes, and start from the live review target in
[README.md current release status](../README.md#current-release-status).

## Flow

| Time | On screen | Talk track |
|---|---|---|
| 0:00-0:30 | Home page | "Library Ops is an interview-demo library management system built to show the current release slice and the control plane around it." |
| 0:30-1:30 | Sign in with a seeded demo account | "The demo accounts are seeded deterministically. That lets an evaluator get straight to the product without setup drift." |
| 1:30-2:30 | Catalog / record detail | "The product keeps works, editions, copies, and loans separate, and exact identifiers stay ahead of broader lexical matches. That gives us a realistic library model without overcomplicating the release." |
| 2:30-3:30 | Architecture or repo/docs view | "The app is a Django system backed by Postgres and deployed on Render. The implementation is organized so product logic, agent control, and evaluator evidence stay separate, with no separate public API layer in the release scope." |
| 3:30-4:30 | Test or validation evidence | "The release is backed by repeatable checks: `npm run checks:precommit`, `npm run verify:core`, `npm run eval:ci`, and the seeded demo commands in the quickstart." |
| 4:30-5:30 | Close on tradeoffs | "We kept the scope focused on the evaluator-ready core: deterministic auth, catalog foundation, lexical search, and deployment evidence. Broader AI or vector-search experiments stay out of the current release." |

## What to emphasize

- Product: a working library-management foundation, not a mock landing page.
- Architecture: Django plus Postgres, with clear separation between domain,
  control plane, and release evidence.
- Tests: the release story is tied to runnable commands, not claims.
- Tradeoffs: prioritize deterministic behavior and evaluator clarity over
  breadth.

## Guardrails

- Use the current release status in `README.md` as the live reference.
- Use [screenshot-matrix.md](./screenshot-matrix.md) as the route-by-route
  evidence checklist before recording or presenting evaluator screenshots.
- Keep the narration concrete and avoid feature walk-through detours that go
  beyond the release bundle.
- If a step fails live, state the failure plainly and move to the next evidence
  point.
