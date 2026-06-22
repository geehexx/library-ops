"""Database-specific keyword-ranking strategies.

Exact identifiers, exact phrases, facets, and stable tie-breaking are backend
independent. Only keyword relevance varies by database: PostgreSQL receives a
weighted full-text document, while other databases return a neutral score and
rely on the portable all-token matcher.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, cast

from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import (
    CombinedSearchVector,
    SearchQuery,
    SearchRank,
    SearchVector,
)
from django.db import connections
from django.db.models import OuterRef, Subquery, TextField, Value
from django.db.models.functions import Cast, Coalesce

from libraryops.catalog.models import BookEdition, WorkContributor

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.db.models.expressions import Combinable

    from libraryops.catalog.models import BibliographicWork

    from .criteria import SearchTerm


class KeywordRankBackend(Protocol):
    """Describe a strategy that produces one keyword-rank expression."""

    def rank_expression(self, term: SearchTerm) -> Combinable:
        """Return a backend-specific relevance expression.

        Args:
            term: Normalized user query.

        Returns:
            A numeric ORM expression where positive values indicate a keyword
            match.
        """

        ...


class KeywordBackendSelector(Protocol):
    """Describe resolution of a keyword backend for a queryset."""

    def resolve(self, queryset: QuerySet[BibliographicWork]) -> KeywordRankBackend:
        """Return the strategy for the queryset's database alias.

        Args:
            queryset: Work queryset whose database alias determines the
                strategy.

        Returns:
            A compatible keyword-ranking backend.
        """

        ...


@dataclass(frozen=True, slots=True)
class PortableKeywordRankBackend:
    """Provide a neutral rank when database full-text search is unavailable."""

    def rank_expression(self, term: SearchTerm) -> Combinable:
        """Return zero because portable matching is handled separately.

        Args:
            term: Normalized user query.

        Returns:
            A constant zero relevance expression.
        """

        _ = term
        return Value(0.0)


@dataclass(frozen=True, slots=True)
class PostgresSearchConfig:
    """Configure PostgreSQL query parsing and rank normalization."""

    text_search_config: str = "english"
    cover_density: bool = False
    normalization: int | None = None


@dataclass(frozen=True, slots=True)
class PostgresKeywordRankBackend:
    """Build a weighted PostgreSQL full-text rank expression.

    Related contributors and editions are aggregated in independent scalar
    subqueries. Keeping those aggregations out of the outer work query avoids
    contributor-by-edition Cartesian multiplication, outer ``GROUP BY``
    requirements, and duplicate work rows.

    Weight policy:

    * ``A`` — title and contributor names;
    * ``B`` — publishers and edition metadata, including subjects;
    * ``C`` — work and edition descriptions.
    """

    config: PostgresSearchConfig = field(default_factory=PostgresSearchConfig)

    def rank_expression(self, term: SearchTerm) -> Combinable:
        """Return a weighted PostgreSQL rank expression.

        Args:
            term: Normalized user query.

        Returns:
            A ``SearchRank`` expression using PostgreSQL web-search syntax.
        """

        search_query = SearchQuery(
            term.text,
            search_type="websearch",
            config=self.config.text_search_config,
        )
        vector = self._search_vector()
        if self.config.normalization is None:
            return SearchRank(
                vector,
                search_query,
                cover_density=self.config.cover_density,
            )
        return SearchRank(
            vector,
            search_query,
            normalization=Value(self.config.normalization),
            cover_density=self.config.cover_density,
        )

    def _search_vector(self) -> CombinedSearchVector:
        """Return the weighted virtual search document."""

        config = self.config.text_search_config
        contributors = self._coalesced_text(self._contributor_text())
        publishers = self._coalesced_text(self._publisher_text())
        metadata = self._coalesced_text(self._edition_metadata_text())
        edition_descriptions = self._coalesced_text(self._edition_description_text())
        vector = (
            SearchVector("title", weight="A", config=config)
            + SearchVector(contributors, weight="A", config=config)
            + SearchVector(publishers, weight="B", config=config)
            + SearchVector(metadata, weight="B", config=config)
            + SearchVector("description", weight="C", config=config)
            + SearchVector(edition_descriptions, weight="C", config=config)
        )
        return cast("CombinedSearchVector", vector)

    @staticmethod
    def _coalesced_text(expression: Subquery) -> Coalesce:
        """Convert a nullable aggregate subquery to non-null text.

        Args:
            expression: Scalar text subquery.

        Returns:
            A text expression safe for ``SearchVector``.
        """

        return Coalesce(expression, Value(""), output_field=TextField())

    @staticmethod
    def _contributor_text() -> Subquery:
        """Aggregate contributor names for one outer work."""

        contributors = (
            WorkContributor.objects.filter(work_id=OuterRef("pk"))
            .order_by()
            .values("work_id")
            .annotate(
                text=StringAgg(
                    "contributor__name",
                    delimiter=" ",
                    distinct=True,
                )
            )
            .values("text")[:1]
        )
        return Subquery(contributors, output_field=TextField())

    @staticmethod
    def _publisher_text() -> Subquery:
        """Aggregate active-edition publishers for one outer work."""

        publishers = (
            BookEdition.objects.filter(
                work_id=OuterRef("pk"),
                archived_at__isnull=True,
            )
            .order_by()
            .values("work_id")
            .annotate(text=StringAgg("publisher", delimiter=" ", distinct=True))
            .values("text")[:1]
        )
        return Subquery(publishers, output_field=TextField())

    @staticmethod
    def _edition_metadata_text() -> Subquery:
        """Aggregate active-edition JSON metadata as searchable text."""

        metadata = (
            BookEdition.objects.filter(
                work_id=OuterRef("pk"),
                archived_at__isnull=True,
            )
            .order_by()
            .values("work_id")
            .annotate(
                text=StringAgg(
                    Cast("external_identifiers", output_field=TextField()),
                    delimiter=" ",
                    distinct=True,
                )
            )
            .values("text")[:1]
        )
        return Subquery(metadata, output_field=TextField())

    @staticmethod
    def _edition_description_text() -> Subquery:
        """Aggregate active-edition descriptions for one outer work."""

        descriptions = (
            BookEdition.objects.filter(
                work_id=OuterRef("pk"),
                archived_at__isnull=True,
            )
            .order_by()
            .values("work_id")
            .annotate(text=StringAgg("description", delimiter=" ", distinct=True))
            .values("text")[:1]
        )
        return Subquery(descriptions, output_field=TextField())


@dataclass(frozen=True, slots=True)
class KeywordBackendResolver:
    """Resolve keyword ranking from the queryset's database alias."""

    portable: PortableKeywordRankBackend = field(default_factory=PortableKeywordRankBackend)
    postgres: PostgresKeywordRankBackend = field(default_factory=PostgresKeywordRankBackend)

    def resolve(self, queryset: QuerySet[BibliographicWork]) -> KeywordRankBackend:
        """Return the strategy matching the queryset connection.

        Using ``queryset.db`` rather than Django's global default connection
        preserves correct behavior for routers, replicas, and explicit
        ``QuerySet.using()`` calls.

        Args:
            queryset: Work queryset whose database alias determines the backend.

        Returns:
            PostgreSQL FTS on PostgreSQL; otherwise the portable strategy.
        """

        vendor = connections[queryset.db].vendor
        return self.postgres if vendor == "postgresql" else self.portable
