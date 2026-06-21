# pyright: reportMissingTypeArgument=false
"""Copy views for the catalog manager slice."""

from __future__ import annotations

from typing import Any

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, UpdateView

from libraryops.catalog import selectors
from libraryops.catalog.forms import CopyForm
from libraryops.catalog.views.base import CatalogMutationView
from libraryops.inventory.models import BookCopy


def _work_id_for_copy(copy: Any) -> int:
    """Return the owning work primary key for one copy."""

    edition = copy.edition
    work_pk = edition.work.pk
    if work_pk is None:
        raise ValueError("Edition is missing an owning work.")
    return work_pk


class CopyCreateView(CatalogMutationView, FormView):
    """Create one copy through a thin manager-backed form view."""

    form_class = CopyForm
    page_title = "Create copy"
    back_url_name = "catalog-detail"
    submit_label = "Create copy"

    def get_initial(self) -> dict[str, Any]:
        """Pre-select the parent edition when creating from an edition detail page."""

        return {"edition": selectors.edition_detail(int(self.kwargs["edition_id"]))}

    def get_back_url_kwargs(self) -> dict[str, Any]:
        """Return the back link for the parent edition's work."""

        edition = selectors.edition_detail(int(self.kwargs["edition_id"]))
        return {"work_id": edition.work.pk}

    def form_valid(self, form: CopyForm) -> Any:
        """Persist one copy and redirect to the parent work detail page."""

        copy = form.apply(actor=self.request.user)
        work_id = _work_id_for_copy(copy)
        return HttpResponseRedirect(reverse("catalog-detail", kwargs={"work_id": work_id}))


class CopyUpdateView(CatalogMutationView, UpdateView):
    """Edit one copy through a thin manager-backed form view."""

    form_class = CopyForm
    page_title = "Edit copy"
    back_url_name = "catalog-detail"
    pk_url_kwarg = "copy_id"
    submit_label = "Save copy"
    context_object_name = "copy"

    def get_queryset(self) -> Any:
        """Return the active copy queryset used for lookups."""

        return selectors.copy_list()

    def get_back_url_kwargs(self) -> dict[str, Any]:
        """Return the back link for the bound copy's work."""

        copy = selectors.copy_detail(int(self.kwargs["copy_id"]))
        return {"work_id": _work_id_for_copy(copy)}

    def form_valid(self, form: CopyForm) -> Any:
        """Persist the copy update and redirect to the parent work detail page."""

        copy = form.apply(actor=self.request.user)
        work_id = _work_id_for_copy(copy)
        return HttpResponseRedirect(reverse("catalog-detail", kwargs={"work_id": work_id}))


class CopyArchiveView(CatalogMutationView, View):
    """Archive one copy via a protected POST action."""

    def post(self, request: Any, copy_id: int, *args: object, **kwargs: object) -> Any:
        """Archive the copy and return to the parent work detail page."""

        copy = selectors.copy_detail(copy_id)
        work_id = _work_id_for_copy(copy)
        BookCopy.objects.archive_copy(actor=request.user, copy=copy)
        return HttpResponseRedirect(reverse("catalog-detail", kwargs={"work_id": work_id}))
