"""Catalog queryset helpers."""

from __future__ import annotations

from django.db import models
from django.db.models import Prefetch

from libraryops.catalog import models as catalog_models
from libraryops.inventory import models as inventory_models


class BibliographicWorkQuerySet(models.QuerySet["catalog_models.BibliographicWork"]):
    """Query helpers for foundation catalog views."""

    def active(self) -> BibliographicWorkQuerySet:
        """Return only non-archived works."""

        return self.filter(archived_at__isnull=True)

    def with_foundation_graph(self) -> BibliographicWorkQuerySet:
        """Prefetch the related foundation graph for evaluator-facing pages."""

        contributor_queryset = catalog_models.WorkContributor.objects.select_related(
            "contributor",
        ).order_by(
            "sort_order",
            "id",
        )
        edition_queryset = catalog_models.BookEdition.objects.filter(
            archived_at__isnull=True,
        ).prefetch_related(
            Prefetch(
                "copies",
                queryset=inventory_models.BookCopy.objects.filter(archived_at__isnull=True),
            )
        )
        return self.prefetch_related(
            Prefetch("work_contributors", queryset=contributor_queryset),
            Prefetch("editions", queryset=edition_queryset),
        )
