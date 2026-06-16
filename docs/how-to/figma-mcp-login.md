# Figma MCP login and fallback

Figma is task-scoped optional for this repo: use it for design tasks when local OAuth and write access exist, but do not fake design output when they do not.

## Login

```bash
codex mcp add figma --url https://mcp.figma.com/mcp || true
codex mcp login figma
codex mcp list
```

## Verification

Use a no-write smoke test first, such as a `whoami` call in a Figma-capable session.

## Write-access rule

Successful OAuth is not enough. If the authenticated account only has view access, record a precise blocker and keep `docs/design/wireframes.md` plus `docs/design/mockup-plan.md` as the canonical fallback.

## Do not store

- Figma OAuth tokens
- private file URLs
- session state
- bearer-token env vars in committed config
