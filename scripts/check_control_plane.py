#!/usr/bin/env python3
"""Validate the Library Ops Codex control plane using only Python's stdlib.

The checker owns static repository contracts. Prompt semantics belong in
Promptfoo, product behavior in product tests, and live tool availability in the
implementation/release preflight.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from collections.abc import Callable

BIDI_CONTROLS: Final = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)
HOOK_SCRIPT_RE: Final = re.compile(r"(?P<path>\.codex/hooks/[A-Za-z0-9_.-]+\.py)")
LOCAL_SCRIPT_RE: Final = re.compile(
    r"(?<![A-Za-z0-9_./-])(scripts/[A-Za-z0-9_.\-/]+\.(?:py|sh))(?![A-Za-z0-9_.\-/])"
)
ADR_LINK_RE: Final = re.compile(r"\((?P<path>\d{4}-[^)]+\.md)\)")


@dataclass(frozen=True, slots=True)
class Issue:
    """One actionable validation failure."""

    code: str
    path: str
    message: str
    remediation: str


class Report:
    """Collect issues while keeping validation code compact."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.issues: list[Issue] = []

    def add(self, code: str, path: Path, message: str, remediation: str) -> None:
        try:
            display = path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            display = str(path)
        self.issues.append(Issue(code, display, message, remediation))

    def require(
        self,
        condition: bool,
        code: str,
        path: Path,
        message: str,
        remediation: str,
    ) -> bool:
        if condition:
            return True
        self.add(code, path, message, remediation)
        return False


def load_contract(path: Path) -> dict[str, Any]:
    """Load the declarative test contract."""
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _path(root: Path, contract: dict[str, Any], section: str, key: str) -> Path:
    value = contract.get(section, {}).get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"contract [{section}] requires non-empty {key}")
    return root / value


def _read_mapping(
    path: Path,
    report: Report,
    code: str,
    loader: Callable[[bytes], Any],
) -> dict[str, Any] | None:
    try:
        value = loader(path.read_bytes())
    except (OSError, ValueError, tomllib.TOMLDecodeError, json.JSONDecodeError) as exc:
        report.add(code, path, f"cannot parse required file: {exc}", "restore valid syntax")
        return None
    if not isinstance(value, dict):
        report.add(code, path, "top-level value must be an object/table", "use a mapping")
        return None
    return value


def _toml(path: Path, report: Report, code: str) -> dict[str, Any] | None:
    return _read_mapping(path, report, code, lambda raw: tomllib.loads(raw.decode("utf-8")))


def _json(path: Path, report: Report, code: str) -> dict[str, Any] | None:
    return _read_mapping(path, report, code, lambda raw: json.loads(raw.decode("utf-8")))


def _string_set(value: Any) -> set[str]:
    return {item for item in value if isinstance(item, str)} if isinstance(value, list) else set()


def check_agents(root: Path, contract: dict[str, Any]) -> list[Issue]:
    """Validate Codex features, permission references, and custom-agent files."""
    report = Report(root)
    config_path = _path(root, contract, "codex", "config")
    agent_dir = _path(root, contract, "codex", "agent_dir")
    config = _toml(config_path, report, "CP100")
    if config is None:
        return report.issues

    hooks_path = _path(root, contract, "codex", "hooks")
    features = config.get("features")
    report.require(
        config.get("hooks") is None,
        "CP101",
        config_path,
        "inline hooks coexist with .codex/hooks.json",
        "keep one hook representation per config layer",
    )
    report.require(
        not hooks_path.exists() or (isinstance(features, dict) and features.get("hooks") is True),
        "CP102",
        config_path,
        "project hooks exist but [features].hooks is not true",
        "set [features] hooks = true",
    )

    permissions_value = config.get("permissions", {})
    permissions = set(permissions_value) if isinstance(permissions_value, dict) else set()

    def check_permission(value: Any, path: Path, owner: str) -> None:
        if isinstance(value, str) and not value.startswith(":") and value not in permissions:
            report.add(
                "CP103",
                path,
                f"{owner} references unknown permission profile {value!r}",
                "define the profile or select an existing one",
            )

    check_permission(config.get("default_permissions"), config_path, "root config")
    agents = config.get("agents")
    if not report.require(
        isinstance(agents, dict),
        "CP104",
        config_path,
        "[agents] table is missing",
        "define named custom-agent roles",
    ):
        return report.issues

    fields = _string_set(contract.get("agents", {}).get("required_string_fields", []))
    referenced: list[Path] = []
    for role, settings in agents.items():
        if not isinstance(settings, dict):
            continue  # scalar [agents] settings such as max_threads
        relative = settings.get("config_file")
        if not isinstance(relative, str) or not relative:
            report.add("CP105", config_path, f"agent {role!r} has no config_file", "add one")
            continue
        target = (config_path.parent / relative).resolve()
        referenced.append(target)
        try:
            target.relative_to(agent_dir.resolve())
        except ValueError:
            report.add(
                "CP106",
                config_path,
                f"agent {role!r} resolves outside {_display(root, agent_dir)}",
                "use agents/<role>.toml relative to .codex/config.toml",
            )
        data = _toml(target, report, "CP107")
        if data is None:
            continue
        for field in fields:
            value = data.get(field)
            if not isinstance(value, str) or not value.strip():
                report.add("CP108", target, f"missing non-empty {field!r}", f"add {field}")
        if isinstance(data.get("name"), str) and data["name"] != role:
            report.add(
                "CP109",
                target,
                f"agent name {data['name']!r} does not match role {role!r}",
                "make name match the [agents.<role>] key",
            )
        check_permission(data.get("default_permissions"), target, f"agent {role!r}")

    for target, count in Counter(referenced).items():
        if count > 1:
            report.add(
                "CP111",
                config_path,
                f"{_display(root, target)} is referenced {count} times",
                "use one file per role",
            )
    configured = set(referenced)
    if agent_dir.is_dir():
        for candidate in sorted(agent_dir.glob("*.toml")):
            if candidate.resolve() not in configured:
                report.add(
                    "CP112",
                    candidate,
                    "orphan custom-agent file",
                    "reference or remove it",
                )
    return report.issues


def _display(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def check_mcps(root: Path, contract: dict[str, Any]) -> list[Issue]:
    """Validate selected MCP transport and required/enabled posture."""
    report = Report(root)
    config_path = _path(root, contract, "codex", "config")
    config = _toml(config_path, report, "CP200")
    if config is None:
        return report.issues
    servers = config.get("mcp_servers")
    if not report.require(
        isinstance(servers, dict) and bool(servers),
        "CP201",
        config_path,
        "no MCP servers are declared",
        "declare the selected servers",
    ):
        return report.issues

    required = _string_set(contract.get("mcp", {}).get("required", []))
    for name in sorted(required - set(servers)):
        report.add("CP202", config_path, f"required MCP {name!r} is absent", "declare it")

    for name, settings in servers.items():
        if not isinstance(settings, dict):
            report.add("CP203", config_path, f"MCP {name!r} is not a table", "use a table")
            continue
        command, url = settings.get("command"), settings.get("url")
        transports = sum(isinstance(value, str) and bool(value.strip()) for value in (command, url))
        if transports != 1:
            report.add(
                "CP204",
                config_path,
                f"MCP {name!r} needs exactly one command or url",
                "choose one transport",
            )
        if isinstance(url, str) and not url.startswith("https://"):
            report.add("CP205", config_path, f"MCP {name!r} URL is not HTTPS", "use https://")
        if settings.get("required") is True and settings.get("enabled") is False:
            report.add(
                "CP206",
                config_path,
                f"MCP {name!r} is required and disabled",
                "enable it or stop requiring it",
            )
        if name in required and settings.get("required") is not True:
            report.add(
                "CP207",
                config_path,
                f"MCP {name!r} is not required = true",
                "restore strict posture after verification",
            )
        args = settings.get("args")
        if args is not None and (
            not isinstance(args, list) or not all(isinstance(item, str) for item in args)
        ):
            report.add(
                "CP208",
                config_path,
                f"MCP {name!r} args are not strings",
                "use a string array",
            )
        tools = settings.get("enabled_tools")
        if tools is not None:
            valid = isinstance(tools, list) and all(
                isinstance(item, str) and item for item in tools
            )
            if not valid or len(tools) != len(set(tools)):
                report.add(
                    "CP209",
                    config_path,
                    f"MCP {name!r} enabled_tools are invalid",
                    "use unique non-empty strings",
                )
        for key in ("startup_timeout_sec", "tool_timeout_sec"):
            value = settings.get(key)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0
            ):
                report.add(
                    "CP210",
                    config_path,
                    f"MCP {name!r} has invalid {key}",
                    "use a positive number",
                )
    return report.issues


def check_hooks(root: Path, contract: dict[str, Any]) -> list[Issue]:
    """Validate hook event policy, handlers, commands, and script paths."""
    report = Report(root)
    hooks_path = _path(root, contract, "codex", "hooks")
    config_path = _path(root, contract, "codex", "config")
    data = _json(hooks_path, report, "CP300")
    config = _toml(config_path, report, "CP301")
    if data is None or config is None:
        return report.issues
    if config.get("hooks") is not None:
        report.add(
            "CP302",
            config_path,
            "inline hooks coexist with hooks.json",
            "remove inline hooks",
        )
    hooks = data.get("hooks")
    if not report.require(
        isinstance(hooks, dict),
        "CP303",
        hooks_path,
        "hooks must be an object",
        "use event arrays",
    ):
        return report.issues

    policy = contract.get("hooks", {})
    allowed = _string_set(policy.get("allowed_events", []))
    required = _string_set(policy.get("required_events", []))
    forbidden = _string_set(policy.get("forbidden_events", []))
    require_root = policy.get("require_git_root_for_project_scripts", True) is True
    forbid_stop_matcher = policy.get("forbid_stop_matcher", True) is True
    for event in sorted(required - set(hooks)):
        report.add("CP304", hooks_path, f"required event {event!r} is absent", "add it")

    seen: set[tuple[str, str]] = set()
    for event, groups in hooks.items():
        if event in forbidden or (allowed and event not in allowed):
            report.add(
                "CP305",
                hooks_path,
                f"event {event!r} is outside policy",
                "remove it or update the contract",
            )
        if not isinstance(groups, list) or not groups:
            report.add(
                "CP306",
                hooks_path,
                f"event {event!r} has no groups",
                "add a non-empty group array",
            )
            continue
        for group in groups:
            if not isinstance(group, dict):
                report.add(
                    "CP307",
                    hooks_path,
                    f"event {event!r} group is not an object",
                    "use an object",
                )
                continue
            matcher = group.get("matcher")
            if matcher is not None:
                if event == "Stop" and forbid_stop_matcher:
                    report.add(
                        "CP308",
                        hooks_path,
                        "Stop matcher is ignored by Codex",
                        "remove it",
                    )
                elif not isinstance(matcher, str):
                    report.add(
                        "CP309",
                        hooks_path,
                        f"{event} matcher is not a string",
                        "use regex text",
                    )
                else:
                    try:
                        re.compile(matcher)
                    except re.error as exc:
                        report.add(
                            "CP310",
                            hooks_path,
                            f"invalid {event} matcher: {exc}",
                            "fix the regex",
                        )
            handlers = group.get("hooks")
            if not isinstance(handlers, list) or not handlers:
                report.add("CP311", hooks_path, f"{event} group has no handlers", "add one")
                continue
            for handler in handlers:
                if not isinstance(handler, dict) or handler.get("type") != "command":
                    report.add(
                        "CP312",
                        hooks_path,
                        f"{event} handler is not type=command",
                        "use a command handler",
                    )
                    continue
                command = handler.get("command")
                if not isinstance(command, str) or not command:
                    report.add(
                        "CP313",
                        hooks_path,
                        f"{event} handler has no command",
                        "add one",
                    )
                    continue
                key = (event, command)
                if key in seen:
                    report.add(
                        "CP314",
                        hooks_path,
                        f"duplicate {event} command",
                        "remove the duplicate",
                    )
                seen.add(key)
                timeout = handler.get("timeout")
                if (
                    isinstance(timeout, bool)
                    or not isinstance(timeout, (int, float))
                    or timeout <= 0
                ):
                    report.add(
                        "CP315",
                        hooks_path,
                        f"{event} command has invalid timeout",
                        "use a positive number",
                    )
                matches = list(HOOK_SCRIPT_RE.finditer(command))
                if ".codex/hooks/" in command and not matches:
                    report.add(
                        "CP316",
                        hooks_path,
                        f"cannot resolve hook script in {command!r}",
                        "use .codex/hooks/<name>.py",
                    )
                for match in matches:
                    script = root / match.group("path")
                    if not script.is_file():
                        report.add(
                            "CP317",
                            script,
                            f"{event} references a missing script",
                            "restore or remove it",
                        )
                    if require_root and "git rev-parse --show-toplevel" not in command:
                        report.add(
                            "CP318",
                            hooks_path,
                            f"{event} project script is not Git-rooted",
                            "resolve from the active worktree",
                        )
    return report.issues


def _frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return result
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip("\"'")
    return {}


def check_skills(root: Path, contract: dict[str, Any]) -> list[Issue]:
    """Validate skill identity and selected reference discoverability."""
    report = Report(root)
    skill_dir = _path(root, contract, "skills", "directory")
    if not report.require(
        skill_dir.is_dir(),
        "CP400",
        skill_dir,
        "skill directory is missing",
        "restore it",
    ):
        return report.issues
    explicit = _string_set(contract.get("skills", {}).get("explicit_reference_skills", []))
    names: Counter[str] = Counter()
    for entrypoint in sorted(skill_dir.glob("*/SKILL.md")):
        directory_name = entrypoint.parent.name
        meta = _frontmatter(entrypoint)
        name, description = meta.get("name", ""), meta.get("description", "")
        if not name or not description:
            report.add(
                "CP401",
                entrypoint,
                "frontmatter needs name and description",
                "add both",
            )
            continue
        names[name] += 1
        if name != directory_name:
            report.add(
                "CP402",
                entrypoint,
                f"name {name!r} != directory {directory_name!r}",
                "make them match",
            )
        readme = entrypoint.parent / "references/README.md"
        if readme.exists():
            report.add(
                "CP403",
                readme,
                "generic reference README weakens discovery",
                "use a descriptive filename",
            )
        if directory_name not in explicit:
            continue
        text = entrypoint.read_text(encoding="utf-8")
        reference_dir = entrypoint.parent / "references"
        for reference in sorted(reference_dir.rglob("*")) if reference_dir.is_dir() else []:
            if reference.is_file():
                relative = reference.relative_to(entrypoint.parent).as_posix()
                if relative not in text and reference.name not in text:
                    report.add(
                        "CP404",
                        reference,
                        "reference is not linked from SKILL.md",
                        f"link {relative}",
                    )
    for name, count in names.items():
        if count > 1:
            report.add(
                "CP405",
                skill_dir,
                f"skill name {name!r} appears {count} times",
                "make names unique",
            )
    return report.issues


def check_adrs(root: Path, contract: dict[str, Any]) -> list[Issue]:
    """Validate exact ADR index/file parity."""
    report = Report(root)
    directory = _path(root, contract, "adrs", "directory")
    index = _path(root, contract, "adrs", "index")
    try:
        text = index.read_text(encoding="utf-8")
    except OSError as exc:
        report.add("CP500", index, f"cannot read ADR index: {exc}", "restore it")
        return report.issues
    files = {path.name for path in directory.glob("[0-9][0-9][0-9][0-9]-*.md")}
    links = {match.group("path") for match in ADR_LINK_RE.finditer(text)}
    for name in sorted(files - links):
        report.add(
            "CP501",
            directory / name,
            "ADR is absent from the index",
            "add an index row",
        )
    for name in sorted(links - files):
        report.add(
            "CP502",
            index,
            f"index links to missing {name}",
            "restore or remove the row",
        )
    return report.issues


def check_bidi_controls(root: Path, contract: dict[str, Any]) -> list[Issue]:
    """Reject hidden bidirectional controls on governance surfaces."""
    report = Report(root)
    patterns = contract.get("security", {}).get("bidi_scan_globs", [])
    scanned: set[Path] = set()
    for pattern in patterns if isinstance(patterns, list) else []:
        if not isinstance(pattern, str):
            continue
        for path in root.glob(pattern):
            if not path.is_file() or path in scanned:
                continue
            scanned.add(path)
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, 1):
                found = sorted({character for character in line if character in BIDI_CONTROLS})
                if found:
                    codes = ", ".join(f"U+{ord(character):04X}" for character in found)
                    report.add(
                        "CP600",
                        path,
                        f"{codes} on line {line_number}",
                        "remove hidden controls",
                    )
    return report.issues


def check_package_scripts(root: Path, contract: dict[str, Any]) -> list[Issue]:
    """Validate repo-local script paths and required runtime wrappers."""
    report = Report(root)
    package_path = _path(root, contract, "package", "file")
    package = _json(package_path, report, "CP700")
    if package is None:
        return report.issues
    scripts = package.get("scripts")
    if not report.require(
        isinstance(scripts, dict),
        "CP701",
        package_path,
        "scripts is not an object",
        "restore it",
    ):
        return report.issues
    for name, command in scripts.items():
        if not isinstance(command, str):
            report.add(
                "CP702",
                package_path,
                f"npm script {name!r} is not a string",
                "use command text",
            )
            continue
        for match in LOCAL_SCRIPT_RE.finditer(command):
            target = root / match.group(1)
            if not target.is_file():
                report.add(
                    "CP703",
                    target,
                    f"npm script {name!r} references a missing file",
                    "restore or update it",
                )
    wrappers = contract.get("package", {}).get("required_wrappers", {})
    for name, fragment in wrappers.items() if isinstance(wrappers, dict) else []:
        command = scripts.get(name)
        if not isinstance(command, str):
            report.add(
                "CP704",
                package_path,
                f"required npm script {name!r} is missing",
                "restore it",
            )
        elif not isinstance(fragment, str) or fragment not in command:
            report.add(
                "CP705",
                package_path,
                f"npm script {name!r} bypasses {fragment!r}",
                "use the wrapper",
            )
    return report.issues


CHECKERS: Final = (
    check_agents,
    check_mcps,
    check_hooks,
    check_skills,
    check_adrs,
    check_bidi_controls,
    check_package_scripts,
)


def collect_issues(root: Path, contract_path: Path | None = None) -> list[Issue]:
    """Run all checks and return deterministic results."""
    root = root.resolve()
    contract = load_contract(
        contract_path.resolve() if contract_path else root / "tests/control_plane/contract.toml"
    )
    issues = [issue for checker in CHECKERS for issue in checker(root, contract)]
    return sorted(issues, key=lambda issue: (issue.code, issue.path, issue.message))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def _human(issues: list[Issue]) -> str:
    if not issues:
        return "control-plane contract: PASS"
    lines = [f"control-plane contract: FAIL ({len(issues)} issue(s))"]
    for issue in issues:
        lines += [
            f"[{issue.code}] {issue.path}: {issue.message}",
            f"  remediation: {issue.remediation}",
        ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    args = _parser().parse_args(argv)
    contract = args.contract
    if contract is not None and not contract.is_absolute():
        contract = args.root / contract
    try:
        issues = collect_issues(args.root, contract)
    except (OSError, TypeError, ValueError, tomllib.TOMLDecodeError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc), "issues": []}, indent=2))
        else:
            print(f"control-plane contract: ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {
                    "ok": not issues,
                    "issue_count": len(issues),
                    "issues": [asdict(issue) for issue in issues],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(_human(issues))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
