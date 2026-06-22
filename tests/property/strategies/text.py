"""Text generators for normalization and search metamorphic relations."""

from __future__ import annotations

from dataclasses import dataclass
from string import ascii_lowercase, digits
from typing import TYPE_CHECKING

from hypothesis import strategies as st

if TYPE_CHECKING:
    from hypothesis.strategies import SearchStrategy


@dataclass(frozen=True, slots=True)
class NormalizationCase:
    """Hold canonical text and a case/whitespace-equivalent spelling."""

    canonical: str
    noisy: str


_TOKEN = st.text(alphabet=ascii_lowercase + digits + "-'_", min_size=1, max_size=16)
_WHITESPACE = st.text(alphabet=(" ", "\t", "\n", "\r", "\v", "\f"), min_size=1, max_size=5)
_OPTIONAL_WHITESPACE = st.one_of(st.just(""), _WHITESPACE)


def _apply_case(token: str, uppercase_mask: list[bool]) -> str:
    """Apply a generated ASCII case mask without changing punctuation."""
    return "".join(
        character.upper() if uppercase else character.lower()
        for character, uppercase in zip(token, uppercase_mask, strict=True)
    )


@st.composite
def normalization_cases(draw: st.DrawFn) -> NormalizationCase:
    """Generate equivalent token sequences with arbitrary case and whitespace."""
    canonical_tokens = draw(st.lists(_TOKEN, min_size=1, max_size=8))
    noisy_tokens = [
        _apply_case(
            token,
            draw(st.lists(st.booleans(), min_size=len(token), max_size=len(token))),
        )
        for token in canonical_tokens
    ]
    separators = draw(
        st.lists(_WHITESPACE, min_size=len(noisy_tokens) - 1, max_size=len(noisy_tokens) - 1)
    )
    prefix = draw(_OPTIONAL_WHITESPACE)
    suffix = draw(_OPTIONAL_WHITESPACE)

    pieces: list[str] = [prefix]
    for index, token in enumerate(noisy_tokens):
        pieces.append(token)
        if index < len(separators):
            pieces.append(separators[index])
    pieces.append(suffix)
    return NormalizationCase(
        canonical=" ".join(canonical_tokens),
        noisy="".join(pieces),
    )


def arbitrary_text() -> SearchStrategy[str]:
    """Return broad Unicode text while excluding surrogate code points."""
    return st.text(
        alphabet=st.characters(blacklist_categories=("Cs",)),
        min_size=0,
        max_size=255,
    )


def whitespace_only() -> SearchStrategy[str]:
    """Return non-empty strings made from Python-recognized ASCII whitespace."""
    return _WHITESPACE


@st.composite
def lexical_query_variants(draw: st.DrawFn, canonical_query: str) -> str:
    """Vary only case and whitespace while retaining token order and content."""
    tokens = canonical_query.split()
    if not tokens:
        raise ValueError("canonical_query must contain a non-whitespace token")

    noisy_tokens = [
        _apply_case(
            token,
            draw(st.lists(st.booleans(), min_size=len(token), max_size=len(token))),
        )
        for token in tokens
    ]
    separators = draw(
        st.lists(_WHITESPACE, min_size=len(noisy_tokens) - 1, max_size=len(noisy_tokens) - 1)
    )
    prefix = draw(_OPTIONAL_WHITESPACE)
    suffix = draw(_OPTIONAL_WHITESPACE)

    pieces: list[str] = [prefix]
    for index, token in enumerate(noisy_tokens):
        pieces.append(token)
        if index < len(separators):
            pieces.append(separators[index])
    pieces.append(suffix)
    return "".join(pieces)
