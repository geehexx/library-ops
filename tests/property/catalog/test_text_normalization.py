"""Algebraic and metamorphic properties for catalog text normalization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hypothesis import event, given
from tests.property.strategies import arbitrary_text, normalization_cases, whitespace_only

from libraryops.catalog.models import normalize_name

if TYPE_CHECKING:
    from tests.property.strategies import NormalizationCase

pytestmark = pytest.mark.property


@given(value=arbitrary_text())
def test_normalize_name_is_idempotent(value: str) -> None:
    """Applying normalization twice must be identical to applying it once."""
    once = normalize_name(value)

    assert normalize_name(once) == once


@given(case=normalization_cases())
def test_case_and_whitespace_noise_preserve_normalized_identity(case: NormalizationCase) -> None:
    """Case and Python-whitespace changes must not change normalized identity."""
    event(f"token_count={len(case.canonical.split())}")

    assert normalize_name(case.noisy) == normalize_name(case.canonical)


@given(value=whitespace_only())
def test_whitespace_only_values_normalize_to_empty(value: str) -> None:
    """Whitespace-only spellings should share the empty normalized identity."""
    assert normalize_name(value) == ""
