#!/usr/bin/env python3
"""Rate-limit repeated narrow shell exploration in favor of symbolic tools."""

import json
import os
import shlex
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VALID_ACTIONS = {"activate", "remind", "cleanup"}
REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = REPO_ROOT / ".codex" / ".runtime" / "serena-hook"

SERENA_NON_SYMBOLIC_SUBSTRINGS = frozenset(
    (
        "pattern",
        "read",
        "diagnostics",
        "memory",
        "onboarding",
        "config",
        "list_file",
        "find_file",
        "shell",
        "dashboard",
        "restart_language_server",
    )
)
GREP_COMMANDS = frozenset(("grep", "rg", "ag", "ack", "fgrep", "egrep", "search_for_pattern"))
READ_COMMANDS = frozenset(
    ("cat", "head", "tail", "sed", "less", "more", "bat", "get-content", "gc")
)
CODE_FILE_EXTENSIONS = frozenset(
    (
        ".al",
        ".bash",
        ".c",
        ".clj",
        ".cljs",
        ".cpp",
        ".cs",
        ".css",
        ".dart",
        ".elm",
        ".ex",
        ".exs",
        ".fs",
        ".fsx",
        ".go",
        ".graphql",
        ".gql",
        ".groovy",
        ".h",
        ".hcl",
        ".hpp",
        ".hs",
        ".html",
        ".java",
        ".jl",
        ".js",
        ".json",
        ".jsonc",
        ".jsx",
        ".kt",
        ".kts",
        ".lean",
        ".lua",
        ".m",
        ".matlab",
        ".md",
        ".php",
        ".proto",
        ".ps1",
        ".py",
        ".r",
        ".rb",
        ".rs",
        ".scala",
        ".sh",
        ".sol",
        ".sql",
        ".svelte",
        ".swift",
        ".tf",
        ".tfvars",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".vue",
        ".yaml",
        ".yml",
        ".zig",
    )
)

GREP_THRESHOLD = 4
READ_THRESHOLD = 4
NON_SYMBOLIC_THRESHOLD = 6
RESET_PERIOD_SECONDS = 900
MIN_DENY_INTERVAL_SECONDS = 60


@dataclass
class ToolUseState:
    """Persist recent hook counters for one Codex session."""

    grep_uses: int = 0
    read_uses: int = 0
    non_symbolic_uses: int = 0
    last_grep_at: str | None = None
    last_read_at: str | None = None
    last_non_symbolic_at: str | None = None
    last_deny_at: str | None = None

    def reset(self) -> None:
        """Reset all exploration counters except the deny timestamp."""
        self.grep_uses = 0
        self.read_uses = 0
        self.non_symbolic_uses = 0
        self.last_grep_at = None
        self.last_read_at = None
        self.last_non_symbolic_at = None


def now_utc() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


def parse_ts(value: str | None) -> datetime | None:
    """Parse an ISO timestamp when present.

    Args:
        value: ISO formatted datetime string or ``None``.

    Returns:
        A timezone-aware ``datetime`` or ``None``.
    """
    if not value:
        return None
    return datetime.fromisoformat(value)


def state_path(session_id: str) -> Path:
    """Return the persisted state path for a session ID."""
    return STATE_ROOT / session_id / "tool_use_state.json"


def load_state(session_id: str) -> ToolUseState:
    """Load persisted hook state for a session.

    Args:
        session_id: Codex session identifier.

    Returns:
        The previously persisted state, or a fresh state on failure.
    """
    path = state_path(session_id)
    try:
        return ToolUseState(**json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return ToolUseState()


def save_state(session_id: str, state: ToolUseState) -> None:
    """Persist hook state for a session.

    Args:
        session_id: Codex session identifier.
        state: State object to serialize.
    """
    path = state_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")


def cleanup_state(session_id: str) -> None:
    """Remove persisted hook state for a session."""
    path = state_path(session_id).parent
    if not path.exists():
        return
    for child in path.iterdir():
        child.unlink(missing_ok=True)
    path.rmdir()


def load_payload() -> dict[str, Any] | None:
    """Load and validate the hook payload from stdin.

    Returns:
        A validated payload mapping, or ``None`` when the payload is unusable.
    """
    raw_input = sys.stdin.read()
    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        print("Serena hook skipped: missing or invalid Codex hook JSON.", file=sys.stderr)
        return None
    if not isinstance(payload, dict) or not payload.get("session_id"):
        print("Serena hook skipped: Codex hook JSON has no session_id.", file=sys.stderr)
        return None
    return payload


def codex_hook_output(reason: str, additional_context: str = "") -> str:
    """Build a Codex pre-tool deny response payload."""
    output: dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    if additional_context:
        output["hookSpecificOutput"]["additionalContext"] = additional_context
    return json.dumps(output)


def session_start_output() -> str:
    """Build the session-start reminder payload for Codex."""
    message = (
        "**IMPORTANT**: If the current directory is a coding project you are working on:"
        " 1. activate it using Serena's activate_project tool unless already done."
        " 2. if you haven't read Serena Instructions Manual yet, do so."
        " Follow this instruction before doing anything else."
    )
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": message,
            }
        }
    )


def is_serena_symbolic_tool(tool_name: str) -> bool:
    """Return whether a tool name maps to symbolic Serena usage."""
    return "serena" in tool_name and not any(
        substring in tool_name for substring in SERENA_NON_SYMBOLIC_SUBSTRINGS
    )


def parse_command(tool_input: dict[str, Any] | None) -> tuple[str | None, list[str]]:
    """Extract a command name and argument list from hook tool input.

    Args:
        tool_input: Raw tool input payload from the hook.

    Returns:
        A tuple of command name and remaining arguments.
    """
    if not tool_input:
        return None, []
    raw_command = str(tool_input.get("cmd") or tool_input.get("command") or "").strip()
    if not raw_command:
        return None, []
    try:
        parts = shlex.split(raw_command)
    except ValueError:
        parts = raw_command.split()
    if not parts:
        return None, []
    return os.path.basename(parts[0]).lower(), parts[1:]


def is_code_file_path(raw_value: str) -> bool:
    """Return whether a shell token looks like a code-like file path."""
    cleaned = raw_value.strip().strip("'\"")
    if not cleaned or cleaned.startswith("-"):
        return False
    return Path(cleaned).suffix.lower() in CODE_FILE_EXTENSIONS


def classify_tool_call(payload: dict[str, Any]) -> str:
    """Classify a tool call into reminder buckets.

    Args:
        payload: Parsed hook payload.

    Returns:
        One of ``symbolic``, ``grep``, ``read``, ``neutral``, or ``reset``.
    """
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "").lower().strip()
    tool_input = payload.get("tool_input") or payload.get("toolInput")

    if is_serena_symbolic_tool(tool_name):
        return "symbolic"

    command_name, command_args = parse_command(tool_input if isinstance(tool_input, dict) else None)
    if command_name in GREP_COMMANDS:
        return "grep"
    if command_name in READ_COMMANDS:
        if any(is_code_file_path(arg) for arg in command_args):
            return "read"
        return "neutral"

    if "serena" in tool_name:
        return "neutral"

    if tool_name in {"bash", "shell", "shell_command"}:
        return "neutral"

    return "reset"


def increment_counter(
    previous_at: str | None, current_value: int, current_time: datetime
) -> tuple[int, str]:
    """Increment or reset a counter based on elapsed time.

    Args:
        previous_at: Previous ISO timestamp for the counter.
        current_value: Previous counter value.
        current_time: Current timestamp.

    Returns:
        Updated counter value and timestamp string.
    """
    previous_dt = parse_ts(previous_at)
    if (
        previous_dt is not None
        and (current_time - previous_dt).total_seconds() <= RESET_PERIOD_SECONDS
    ):
        return current_value + 1, current_time.isoformat()
    return 1, current_time.isoformat()


def should_rate_limit(state: ToolUseState, current_time: datetime) -> bool:
    """Return whether the hook should suppress repeated deny messages."""
    last_deny = parse_ts(state.last_deny_at)
    if last_deny is None:
        return False
    return (current_time - last_deny).total_seconds() < MIN_DENY_INTERVAL_SECONDS


def remind(session_id: str, payload: dict[str, Any]) -> int:
    """Apply reminder logic for one pre-tool hook event.

    Args:
        session_id: Codex session identifier.
        payload: Parsed hook payload.

    Returns:
        Zero after either updating state or printing a deny payload.
    """
    state = load_state(session_id)
    current_time = now_utc()

    if should_rate_limit(state, current_time):
        return 0

    classification = classify_tool_call(payload)

    if classification in {"symbolic", "reset"}:
        state.reset()
        save_state(session_id, state)
        return 0

    if classification == "neutral":
        return 0

    if classification == "grep":
        state.grep_uses, state.last_grep_at = increment_counter(
            state.last_grep_at, state.grep_uses, current_time
        )
    elif classification == "read":
        state.read_uses, state.last_read_at = increment_counter(
            state.last_read_at, state.read_uses, current_time
        )

    state.non_symbolic_uses, state.last_non_symbolic_at = increment_counter(
        state.last_non_symbolic_at, state.non_symbolic_uses, current_time
    )

    deny_reason: str | None = None
    additional_context: str = ""
    if classification == "grep" and state.grep_uses >= GREP_THRESHOLD:
        deny_reason = (
            "Too many consecutive grep-style shell searches without a symbolic-tool reset. "
            "Use Serena, code-review-graph, ast-grep, or one batched shell search before retrying."
        )
        additional_context = (
            "The repo reminder only engages after repeated grep-style shell searches. "
            "Reset it by using Serena symbolic tools, a broader graph/symbol pass, "
            "or a specialist packet instead of widening root-local exploration."
        )
    elif classification == "read" and state.read_uses >= READ_THRESHOLD:
        deny_reason = (
            "Too many consecutive code-file reads without a symbolic-tool reset. "
            "Use Serena symbol reads, code-review-graph, or one batched shell read before retrying."
        )
        additional_context = (
            "The reminder targets repeated narrow file reads of code-like files. "
            "Symbol-aware reads should reset this counter, and specialist routing "
            "should take over before the root keeps broadening the read loop."
        )
    elif state.non_symbolic_uses >= NON_SYMBOLIC_THRESHOLD:
        deny_reason = (
            "Too many consecutive non-symbolic shell inspections. "
            "Use Serena, code-review-graph, or ast-grep to reset the "
            "exploration mode before retrying."
        )
        additional_context = (
            "Mixed grep/read shell bursts are intentionally throttled so the workflow shifts "
            "back to symbolic or graph tooling, or to a specialist packet when the root "
            "is trying to keep expanding direct tool use."
        )

    if deny_reason is None:
        save_state(session_id, state)
        return 0

    state.reset()
    state.last_deny_at = current_time.isoformat()
    save_state(session_id, state)
    print(codex_hook_output(deny_reason, additional_context))
    return 0


def main() -> int:
    """Dispatch the Serena hook subcommands.

    Returns:
        Zero for all handled hook paths.
    """
    if len(sys.argv) != 2 or sys.argv[1] not in VALID_ACTIONS:
        print("usage: serena_hook.py activate|remind|cleanup", file=sys.stderr)
        return 0

    payload = load_payload()
    if payload is None:
        return 0

    session_id = str(payload["session_id"])
    action = sys.argv[1]

    if action == "activate":
        print(session_start_output())
        return 0

    if action == "cleanup":
        cleanup_state(session_id)
        return 0

    return remind(session_id, payload)


if __name__ == "__main__":
    raise SystemExit(main())
