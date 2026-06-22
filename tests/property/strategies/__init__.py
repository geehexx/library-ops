"""Reusable, shrink-friendly strategies for property tests."""

from tests.property.strategies.isbn import (
    InvalidISBNCase,
    ISBNCase,
    invalid_checksum_cases,
    isbn13_format_variants,
    valid_isbn_cases,
)
from tests.property.strategies.text import (
    NormalizationCase,
    arbitrary_text,
    lexical_query_variants,
    normalization_cases,
    whitespace_only,
)

__all__ = [
    "ISBNCase",
    "InvalidISBNCase",
    "NormalizationCase",
    "arbitrary_text",
    "invalid_checksum_cases",
    "isbn13_format_variants",
    "lexical_query_variants",
    "normalization_cases",
    "valid_isbn_cases",
    "whitespace_only",
]
