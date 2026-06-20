# Screenshot Matrix

Use this matrix as the evaluator-facing route inventory for release evidence.
It tracks which user-visible surfaces already have browser-backed proof, which
ones have tracked visual baselines, and which still need follow-up under
`16.3` or the external social-auth blocker `16.6`.

## Status Legend

- `covered`: browser flow and release evidence already exist.
- `partial`: browser assertions exist, but no dedicated screenshot/baseline or
  no single evaluator-ready artifact exists yet.
- `missing`: route/state still needs explicit release-evidence capture.
- `blocked`: requires external provider or hosted-environment proof.

## Route Matrix

| Route / surface | Primary roles / states | Current evidence | Status | Follow-up |
|---|---|---|---|---|
| `/` home | anonymous | `tests/e2e/test_auth_surface.py` with baseline `auth_surface/default/home.png` | covered | none |
| `/accounts/login/` password-only | anonymous | `tests/e2e/test_auth_surface.py` with baseline `auth_surface/default/login.png` | covered | none |
| `/accounts/login/` provider-enabled | anonymous, Google/GitHub enabled | `tests/e2e/test_auth_surface.py` with baseline `auth_surface/providers/login.png` | covered | live callback proof still belongs to `16.6` |
| signed-in home | librarian | `tests/e2e/test_auth_surface.py` with baseline `auth_surface/default/signed-in.png` | covered | none |
| permission-denied create flow `/catalog/create/` | member denied | `tests/e2e/test_navigation.py` with baseline `navigation/denied/create-flow.png` | covered | none |
| `/catalog/` search results | anonymous exact-identifier path | `tests/e2e/test_circulation_search.py` with baseline `circulation_search/exact-isbn-ranking.png` | covered | none |
| `/catalog/<work_id>/` detail | member and librarian | `tests/e2e/test_catalog_navigation.py` browser assertions | partial | add explicit screenshot evidence if the detail page enters the final evaluator deck |
| archive confirmation states on catalog detail | librarian confirm/cancel flows | `tests/e2e/test_catalog_navigation.py` browser assertions | partial | add explicit screenshot evidence for destructive confirmation states |
| `/catalog/create/` manager happy path | librarian validation, create form, and success redirect | `tests/e2e/test_navigation.py` browser assertions for validation and successful record creation | partial | add evaluator-ready screenshot for create/edit submit-confirm path if the final reviewer deck requires it |
| `/circulation/` dashboard | librarian empty and post-return states | `tests/e2e/test_circulation_search.py` with baseline `circulation_search/checkout-return-dashboard.png` | covered | none |
| `/circulation/checkout/` dialog | librarian | `tests/e2e/test_circulation_search.py` with baseline `circulation_search/checkout-form.png` | covered | none |
| `/circulation/return/` dialog | librarian | `tests/e2e/test_circulation_search.py` browser assertions through return workflow | partial | add dedicated screenshot only if the return dialog must appear in evaluator evidence |
| `/admin/` | admin | Django admin route is in the inventory; browser evidence should live in `tests/e2e/test_navigation.py` once the dedicated route check lands | partial | keep out of the final evaluator deck unless the dedicated admin route check fails or product scope changes |
| `/health/` | evaluator / release operator | `tests/smoke/test_django_bootstrap.py` already proves `/health/` returns `ok`; route is also referenced by README and Render blueprint checks | covered | none unless hosted `/health/` proof drifts |
| social-auth callback completion | Google and GitHub local + Render | blocked by provider-console / Render / SocialApp state | blocked | close under `16.6` with live callback evidence |

## Notes

- This matrix is intentionally route-inventory driven. It should not claim
  idealized screens or flows that do not exist on the current branch.
- Tracked visual baselines live under `tests/e2e/visual_baselines/`; runtime
  captures and diffs stay under `output/playwright/`.
- If a missing surface needs product code changes, route that work into a
  bounded follow-on task instead of widening the evidence lane.
