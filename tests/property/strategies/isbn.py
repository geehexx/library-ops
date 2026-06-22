"""Shrink-friendly ISBN generators with an independent checksum oracle.

The strategy layer never calls ``libraryops.catalog.models.clean_isbn`` or the
factory helper ``tests.factories.build_isbn13``. Reusing either implementation
would permit the same checksum defect on both sides of an assertion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from hypothesis import strategies as st

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hypothesis.strategies import SearchStrategy

type ISBNKind = Literal["isbn10", "isbn13"]


@dataclass(frozen=True, slots=True)
class ISBNCase:
    """Describe one valid raw ISBN and its independently derived identity."""

    raw: str
    compact_input: str
    canonical13: str
    kind: ISBNKind


@dataclass(frozen=True, slots=True)
class InvalidISBNCase:
    """Describe one valid-shaped ISBN with a guaranteed wrong check digit."""

    raw: str
    kind: ISBNKind


def _isbn13_check_digit(payload: str) -> str:
    """Return the ISBN-13 check digit for a twelve-digit payload."""
    total = sum((1 if index % 2 == 0 else 3) * int(digit) for index, digit in enumerate(payload))
    return str((10 - (total % 10)) % 10)


def _isbn10_check_digit(payload: str) -> str:
    """Return the ISBN-10 check character for a nine-digit payload."""
    weighted_total = sum((10 - index) * int(digit) for index, digit in enumerate(payload))
    check_value = (-weighted_total) % 11
    return "X" if check_value == 10 else str(check_value)


def _isbn10_to_isbn13(compact10: str) -> str:
    """Convert a checksum-valid compact ISBN-10 to canonical ISBN-13."""
    payload = f"978{compact10[:9]}"
    return f"{payload}{_isbn13_check_digit(payload)}"


def _decorate(compact: str, separators: Sequence[str]) -> str:
    """Insert one generated separator between every adjacent character."""
    pieces: list[str] = []
    for index, character in enumerate(compact):
        pieces.append(character)
        if index < len(separators):
            pieces.append(separators[index])
    return "".join(pieces)


_SEPARATOR = st.sampled_from(("", " ", "-"))
_EDGE_WHITESPACE = st.sampled_from(("", " ", "\t", "\n"))


@st.composite
def valid_isbn13_cases(draw: st.DrawFn) -> ISBNCase:
    """Generate valid 978/979 ISBN-13 values with supported formatting noise."""
    prefix = draw(st.sampled_from(("978", "979")))
    body = draw(st.lists(st.integers(min_value=0, max_value=9), min_size=9, max_size=9))
    payload = prefix + "".join(str(digit) for digit in body)
    compact = f"{payload}{_isbn13_check_digit(payload)}"
    separators = draw(st.lists(_SEPARATOR, min_size=12, max_size=12))
    prefix_noise = draw(_EDGE_WHITESPACE)
    suffix_noise = draw(_EDGE_WHITESPACE)
    raw = f"{prefix_noise}{_decorate(compact, separators)}{suffix_noise}"
    return ISBNCase(raw=raw, compact_input=compact, canonical13=compact, kind="isbn13")


@st.composite
def valid_isbn10_cases(draw: st.DrawFn) -> ISBNCase:
    """Generate valid ISBN-10 values, including lower-case and upper-case ``X``."""
    digits = draw(st.lists(st.integers(min_value=0, max_value=9), min_size=9, max_size=9))
    payload = "".join(str(digit) for digit in digits)
    compact = f"{payload}{_isbn10_check_digit(payload)}"
    displayed = compact
    if compact.endswith("X") and draw(st.booleans()):
        displayed = f"{compact[:-1]}x"
    separators = draw(st.lists(_SEPARATOR, min_size=9, max_size=9))
    prefix_noise = draw(_EDGE_WHITESPACE)
    suffix_noise = draw(_EDGE_WHITESPACE)
    raw = f"{prefix_noise}{_decorate(displayed, separators)}{suffix_noise}"
    return ISBNCase(
        raw=raw,
        compact_input=compact,
        canonical13=_isbn10_to_isbn13(compact),
        kind="isbn10",
    )


def valid_isbn_cases() -> SearchStrategy[ISBNCase]:
    """Return a strategy spanning both supported ISBN checksum schemes."""
    return st.one_of(valid_isbn10_cases(), valid_isbn13_cases())


@st.composite
def invalid_checksum_cases(draw: st.DrawFn) -> InvalidISBNCase:
    """Change only a valid ISBN's check digit, guaranteeing invalidity."""
    valid = draw(valid_isbn_cases())
    compact = valid.compact_input
    alphabet = "0123456789X" if valid.kind == "isbn10" else "0123456789"
    wrong = draw(st.sampled_from(tuple(value for value in alphabet if value != compact[-1])))
    invalid = f"{compact[:-1]}{wrong}"
    separators = draw(st.lists(_SEPARATOR, min_size=len(invalid) - 1, max_size=len(invalid) - 1))
    return InvalidISBNCase(raw=_decorate(invalid, separators), kind=valid.kind)


@st.composite
def isbn13_format_variants(draw: st.DrawFn, canonical13: str) -> str:
    """Generate supported formatting variants of one known ISBN-13."""
    if len(canonical13) != 13 or not canonical13.isdigit():
        raise ValueError("canonical13 must contain exactly thirteen digits")
    separators = draw(st.lists(_SEPARATOR, min_size=12, max_size=12))
    prefix_noise = draw(_EDGE_WHITESPACE)
    suffix_noise = draw(_EDGE_WHITESPACE)
    return f"{prefix_noise}{_decorate(canonical13, separators)}{suffix_noise}"
