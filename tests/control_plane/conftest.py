"""Shared fixtures for control-plane tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root from the test location."""
    return Path(__file__).resolve().parents[2]
