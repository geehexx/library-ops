# Unit Tests Rules

- Follow `tests/AGENTS.md` first.
- This subtree owns pure model, selector, form, helper, and invariant tests
  that do not need browser automation.
- Keep modules narrow and kind-first under `tests/unit/<domain>/`.
- Move DB-heavy orchestration or permission-sensitive flows to
  `tests/integration/` instead of broadening unit coverage.
