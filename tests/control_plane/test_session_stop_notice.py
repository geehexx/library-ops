from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from types import ModuleType

    import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = REPO_ROOT / ".codex" / "hooks" / "session_stop_notice.py"


def load_hook_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("session_stop_notice", HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_session_stop_notice_prints_expected_summary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    hook: Any = load_hook_module()

    assert hook.main() == 0
    out = capsys.readouterr().out
    assert "Session close:" in out
    assert "source-of-truth docs used" in out
    assert "skills used" in out
    assert "retrospective updates" in out
