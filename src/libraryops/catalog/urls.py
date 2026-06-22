"""Catalog URL configuration."""

from __future__ import annotations

from django.urls import path

from libraryops.catalog.views import (
    CatalogCreateView,
    CatalogDetailView,
    CatalogIndexView,
    CopyArchiveView,
    CopyCreateView,
    CopyUpdateView,
    EditionArchiveView,
    EditionCreateView,
    EditionUpdateView,
    WorkArchiveView,
    WorkCreateView,
    WorkUpdateView,
)

urlpatterns = [
    path("", CatalogIndexView.as_view(), name="catalog-index"),
    path("<int:work_id>/", CatalogDetailView.as_view(), name="catalog-detail"),
    path("create/", CatalogCreateView.as_view(), name="catalog-create"),
    path("works/create/", WorkCreateView.as_view(), name="work-create"),
    path("works/<int:work_id>/edit/", WorkUpdateView.as_view(), name="work-edit"),
    path("works/<int:work_id>/archive/", WorkArchiveView.as_view(), name="work-archive"),
    path(
        "works/<int:work_id>/editions/create/",
        EditionCreateView.as_view(),
        name="edition-create",
    ),
    path(
        "editions/<int:edition_id>/edit/",
        EditionUpdateView.as_view(),
        name="edition-edit",
    ),
    path(
        "editions/<int:edition_id>/archive/",
        EditionArchiveView.as_view(),
        name="edition-archive",
    ),
    path("editions/<int:edition_id>/copies/create/", CopyCreateView.as_view(), name="copy-create"),
    path("copies/<int:copy_id>/edit/", CopyUpdateView.as_view(), name="copy-edit"),
    path("copies/<int:copy_id>/archive/", CopyArchiveView.as_view(), name="copy-archive"),
]
