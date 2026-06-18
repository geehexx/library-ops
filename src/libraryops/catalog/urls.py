"""Catalog URL configuration."""

from __future__ import annotations

from django.urls import path

from libraryops.catalog.views import CatalogCreateView, CatalogDetailView, CatalogIndexView

urlpatterns = [
    path("", CatalogIndexView.as_view(), name="catalog-index"),
    path("<int:work_id>/", CatalogDetailView.as_view(), name="catalog-detail"),
    path("create/", CatalogCreateView.as_view(), name="catalog-create"),
]
