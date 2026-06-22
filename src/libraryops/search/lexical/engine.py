"""Object-oriented orchestration for lexical catalog search."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.db import connections

from .backends import KeywordBackendResolver, KeywordBackendSelector
from .facets import CatalogFacetFilter
from .ranking import DeterministicRankingPolicy

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from libraryops.catalog.models import BibliographicWork

    from .criteria import CatalogSearchCriteria


@dataclass(frozen=True, slots=True)
class CatalogSearchEngine:
    """Compose facet filtering, backend selection, and ranking policy.

    The engine is stateless and safe to reuse. It does not own the catalog base
    queryset: callers decide which work population, eager-loading policy, and
    database alias search is allowed to operate over.
    """

    facet_filter: CatalogFacetFilter = field(default_factory=CatalogFacetFilter)
    backend_selector: KeywordBackendSelector = field(default_factory=KeywordBackendResolver)
    ranking_policy: DeterministicRankingPolicy = field(default_factory=DeterministicRankingPolicy)

    def search(
        self,
        queryset: QuerySet[BibliographicWork],
        criteria: CatalogSearchCriteria,
    ) -> QuerySet[BibliographicWork]:
        """Build one lazy catalog-search queryset.

        Args:
            queryset: Caller-owned active work queryset.
            criteria: Normalized query and facets.

        Returns:
            A lazy facet-filtered queryset. Non-empty terms also receive
            deterministic rank, keyword score, and explanation annotations.
        """

        vendor = connections[queryset.db].vendor
        filtered = self.facet_filter.apply(
            queryset,
            criteria.facets,
            database_vendor=vendor,
        )
        if criteria.term.is_empty:
            return filtered
        return self.ranking_policy.apply(
            filtered,
            criteria.term,
            keyword_backend=self.backend_selector.resolve(filtered),
        )
