"""Private test helpers for loading repo-owned scripts."""

from __future__ import annotations

import importlib.util
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType


def load_repo_module(repo_root: Path, relative_path: str, module_name: str) -> ModuleType:
    """Load one repo-owned Python script without requiring it to be a package."""
    path = repo_root / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
