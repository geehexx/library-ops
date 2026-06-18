# pyright: reportMissingTypeArgument=false
"""Shared catalog views for the foundation and manager slice."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView

from libraryops.accounts.permissions import CatalogManagerRequiredMixin, RoleContextMixin
from libraryops.catalog import selectors
from libraryops.catalog.forms import CatalogFoundationCreateForm
from libraryops.catalog.models import BibliographicWork


class CatalogIndexView(RoleContextMixin, ListView):
    """Render the read-only foundation catalog index."""

    context_object_name = "works"
    template_name = "catalog/index.html"

    def get_queryset(self) -> Any:
        """Return the read-optimized foundation queryset."""

        return selectors.work_list()


class CatalogDetailView(RoleContextMixin, DetailView):
    """Render one foundation work with related contributors and copies."""

    context_object_name = "work"
    pk_url_kwarg = "work_id"
    template_name = "catalog/detail.html"

    def get_queryset(self) -> Any:
        """Return the foundation queryset used for detail lookups."""

        return selectors.work_list()


class CatalogCreateView(CatalogManagerRequiredMixin, FormView):
    """Render and process the protected Phase 1 foundation create flow."""

    form_class = CatalogFoundationCreateForm
    form_success_url = ""
    template_name = "catalog/create.html"

    def form_valid(self, form: CatalogFoundationCreateForm) -> Any:
        """Persist the foundation record graph and redirect to the detail page."""

        if not isinstance(self.request.user, User):
            raise PermissionDenied("Catalog mutations require an authenticated user.")
        work = BibliographicWork.objects.create_foundation_record(
            actor=self.request.user,
            data=form.to_payload(),
        )
        self.form_success_url = reverse("catalog-detail", kwargs={"work_id": work.pk})
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return the detail URL for the newly created foundation work."""

        return str(self.form_success_url)


class CatalogMutationView(CatalogManagerRequiredMixin):
    """Shared context helpers for manager-only catalog form pages."""

    template_name = "catalog/form.html"
    page_title = ""
    submit_label = "Save changes"
    back_label = "Back"
    back_url_name = "catalog-index"

    def get_back_url_kwargs(self) -> dict[str, Any]:
        """Return the reverse kwargs for the back link."""

        return {}

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Attach the shared form page labels and back link."""

        context = super().get_context_data(**kwargs)
        context.setdefault("page_title", self.page_title)
        context.setdefault("submit_label", self.submit_label)
        context.setdefault("back_label", self.back_label)
        context.setdefault(
            "back_url",
            reverse(self.back_url_name, kwargs=self.get_back_url_kwargs()),
        )
        return context
