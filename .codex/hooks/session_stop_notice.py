#!/usr/bin/env python3
"""Emit a concise session-close reminder for this repo."""


def main() -> int:
    """Print the required end-of-session summary fields.

    Returns:
        Zero for normal hook completion.
    """
    print(
        "Session close: summarize Task ID, source-of-truth docs used, skills used, "
        "subagents used and their status, elicitation path used, files changed, "
        "decision status/user tie-back, manual user-run setup commands requested, "
        "required tools used, raw evidence captured, checks run, risks, cleanup performed, "
        "and retrospective updates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
