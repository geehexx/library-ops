"""Value objects that normalize lexical-search input at the boundary.

The search engine accepts immutable criteria rather than a loose collection of
strings. Normalization therefore happens once, before any ORM expression is
built, and every later component receives the same canonical values.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from django.core.exceptions import ValidationError

from libraryops.catalog.models import clean_isbn, normalize_name

_TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(r"[\w]+(?:'[\w]+)?", re.UNICODE)
_IDENTIFIER_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<prefix>[a-z][a-z-]*)\s*:\s*(?P<value>.+)$",
    re.IGNORECASE,
)
_PORTABLE_TOKEN_LIMIT: Final[int] = 16
_JSON_INTEGER_MAX_DIGITS: Final[int] = 18


def _collapse_whitespace(value: str | None) -> str:
    """Return text with leading, trailing, and repeated whitespace removed.

    Args:
        value: Raw user or query-string value.

    Returns:
        A stable single-space representation. Missing values become an empty
        string.
    """

    return " ".join((value or "").strip().split())


def _clean_optional(value: str | None) -> str | None:
    """Normalize an optional value and convert blank text to ``None``.

    Args:
        value: Raw optional value.

    Returns:
        Whitespace-collapsed text, or ``None`` when no value remains.
    """

    cleaned = _collapse_whitespace(value)
    return cleaned or None


class Availability(StrEnum):
    """Supported inventory-state facets."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"

    @classmethod
    def parse(cls, value: str | None) -> Availability | None:
        """Parse an availability value without making unknown input fatal.

        Browser query strings are untrusted input. An unsupported value is
        treated as an absent facet instead of raising from a read-only search.

        Args:
            value: Raw availability facet.

        Returns:
            A supported availability member, or ``None`` for blank or unknown
            input.
        """

        cleaned = _clean_optional(value)
        if cleaned is None:
            return None
        try:
            return cls(cleaned.casefold())
        except ValueError:
            return None


class IdentifierNamespace(StrEnum):
    """Optional namespace supplied through an exact-identifier prefix."""

    ISBN = "isbn"
    BARCODE = "barcode"
    EXTERNAL = "external"

    @classmethod
    def parse(cls, value: str) -> IdentifierNamespace | None:
        """Map supported prefix aliases to an identifier namespace.

        Args:
            value: Prefix text before the colon.

        Returns:
            The matching namespace, or ``None`` when the prefix is not a
            supported identifier qualifier.
        """

        aliases = {
            "isbn": cls.ISBN,
            "barcode": cls.BARCODE,
            "id": cls.EXTERNAL,
            "external": cls.EXTERNAL,
            "external-id": cls.EXTERNAL,
            "source": cls.EXTERNAL,
            "source-id": cls.EXTERNAL,
        }
        return aliases.get(value.casefold())


@dataclass(frozen=True, slots=True)
class SearchTerm:
    """Represent canonical free text and exact-identifier candidates.

    Supported prefixes such as ``barcode:COPY-0001`` are removed before
    matching and retained as ``identifier_namespace`` so unrelated identifier
    lookups can be skipped. Unqualified input remains eligible for every exact
    identifier namespace.

    ``tokens`` are used only by the portable fallback. PostgreSQL receives the
    complete normalized text through ``websearch_to_tsquery``. Capping the
    fallback at sixteen unique tokens bounds SQLite expression growth while
    preserving the original text for PostgreSQL and exact matching.
    """

    text: str
    normalized_phrase: str
    tokens: tuple[str, ...]
    identifier_namespace: IdentifierNamespace | None
    exact_isbn: str | None
    numeric_identifier: int | None

    @classmethod
    def from_value(cls, value: str | None) -> SearchTerm:
        """Build a normalized term from user-entered text.

        Args:
            value: Raw free text or prefixed exact identifier.

        Returns:
            An immutable normalized term.
        """

        raw_text = _collapse_whitespace(value)
        namespace, text = cls._split_identifier_prefix(raw_text)
        normalized_phrase = normalize_name(text) if text else ""
        return cls(
            text=text,
            normalized_phrase=normalized_phrase,
            tokens=cls._tokens(normalized_phrase),
            identifier_namespace=namespace,
            exact_isbn=cls._exact_isbn(text, namespace=namespace),
            numeric_identifier=cls._numeric_identifier(text),
        )

    @property
    def is_empty(self) -> bool:
        """Return whether no searchable text was supplied."""

        return not self.text

    @property
    def permits_isbn(self) -> bool:
        """Return whether ISBN matching applies to this term."""

        return self.identifier_namespace in {None, IdentifierNamespace.ISBN}

    @property
    def permits_barcode(self) -> bool:
        """Return whether barcode matching applies to this term."""

        return self.identifier_namespace in {None, IdentifierNamespace.BARCODE}

    @property
    def permits_external_identifier(self) -> bool:
        """Return whether provenance and metadata identifier matching applies."""

        return self.identifier_namespace in {None, IdentifierNamespace.EXTERNAL}

    @staticmethod
    def _split_identifier_prefix(
        value: str,
    ) -> tuple[IdentifierNamespace | None, str]:
        """Extract a supported identifier prefix from normalized text.

        Args:
            value: Whitespace-collapsed user input.

        Returns:
            The parsed namespace and searchable payload. Unsupported prefixes
            remain part of ordinary free text.
        """

        match = _IDENTIFIER_PREFIX_PATTERN.fullmatch(value)
        if match is None:
            return None, value
        namespace = IdentifierNamespace.parse(match.group("prefix"))
        if namespace is None:
            return None, value
        payload = _collapse_whitespace(match.group("value"))
        if not payload:
            return None, value
        return namespace, payload

    @staticmethod
    def _tokens(value: str) -> tuple[str, ...]:
        """Return de-duplicated fallback tokens in first-occurrence order.

        Args:
            value: Case-folded, whitespace-normalized text.

        Returns:
            At most sixteen Unicode word tokens.
        """

        unique_tokens = dict.fromkeys(match.group(0) for match in _TOKEN_PATTERN.finditer(value))
        return tuple(unique_tokens)[:_PORTABLE_TOKEN_LIMIT]

    @staticmethod
    def _numeric_identifier(value: str) -> int | None:
        """Return a bounded ASCII integer candidate for JSON identifiers.

        Args:
            value: Prefix-free normalized query text.

        Returns:
            An integer for a short ASCII-decimal value, or ``None`` otherwise.
        """

        if (
            not value
            or not value.isascii()
            or not value.isdecimal()
            or len(value) > _JSON_INTEGER_MAX_DIGITS
        ):
            return None
        return int(value)

    @staticmethod
    def _exact_isbn(
        value: str,
        *,
        namespace: IdentifierNamespace | None,
    ) -> str | None:
        """Return canonical ISBN-13 digits for a valid candidate.

        Args:
            value: Prefix-free normalized text.
            namespace: Optional identifier namespace.

        Returns:
            Canonical ISBN-13 digits, or ``None`` for non-ISBN input.
        """

        if not value or namespace not in {None, IdentifierNamespace.ISBN}:
            return None
        try:
            return clean_isbn(value)
        except ValidationError:
            return None


@dataclass(frozen=True, slots=True)
class CatalogFacets:
    """Hold normalized, independently composable catalog facets."""

    availability: Availability | None = None
    contributor: str | None = None
    subject: str | None = None
    language: str | None = None
    source: str | None = None

    @classmethod
    def from_values(
        cls,
        *,
        availability: str | None = None,
        contributor: str | None = None,
        subject: str | None = None,
        language: str | None = None,
        source: str | None = None,
    ) -> CatalogFacets:
        """Normalize facet values at the selector or HTTP boundary.

        Args:
            availability: Requested inventory state.
            contributor: Contributor display name.
            subject: Subject label from edition metadata.
            language: Edition language code.
            source: Provenance source name.

        Returns:
            An immutable facet selection.
        """

        return cls(
            availability=Availability.parse(availability),
            contributor=_clean_optional(contributor),
            subject=_clean_optional(subject),
            language=_clean_optional(language),
            source=_clean_optional(source),
        )


@dataclass(frozen=True, slots=True)
class CatalogSearchCriteria:
    """Bundle a lexical term with optional catalog facets."""

    term: SearchTerm
    facets: CatalogFacets

    @classmethod
    def from_values(
        cls,
        query: str | None = None,
        *,
        availability: str | None = None,
        contributor: str | None = None,
        subject: str | None = None,
        language: str | None = None,
        source: str | None = None,
    ) -> CatalogSearchCriteria:
        """Build complete criteria from selector or query-string values.

        Args:
            query: Free text or exact identifier.
            availability: Requested inventory state.
            contributor: Contributor display name.
            subject: Subject label from edition metadata.
            language: Edition language code.
            source: Provenance source name.

        Returns:
            Normalized immutable search criteria.
        """

        return cls(
            term=SearchTerm.from_value(query),
            facets=CatalogFacets.from_values(
                availability=availability,
                contributor=contributor,
                subject=subject,
                language=language,
                source=source,
            ),
        )
