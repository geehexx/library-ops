# pyright: reportMissingTypeArgument=false
"""Edition views for the catalog manager slice."""

from __future__ import annotations

from typing import Any

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, UpdateView

from libraryops.catalog import selectors
from libraryops.catalog.forms import EditionForm
from libraryops.catalog.models import BookEdition
from libraryops.catalog.views.base import CatalogMutationView


class EditionCreateView(CatalogMutationView, FormView):
    """Create one edition through a thin manager-backed form view."""

    form_class = EditionForm
    page_title = "Create edition"
    submit_label = "Create edition"

    def get_initial(self) -> dict[str, Any]:
        """Pre-select the parent work when creating from a work detail page."""

        return {"work": selectors.work_detail(int(self.kwargs["work_id"]))}

    def get_back_url_kwargs(self) -> dict[str, Any]:
        """Return the back link for the parent work."""

        return {"work_id": int(self.kwargs["work_id"])}

    def form_valid(self, form: EditionForm) -> Any:
        """Persist one edition and redirect to the parent work detail page."""

        edition = form.apply(actor=self.request.user)
        return HttpResponseRedirect(reverse("catalog-detail", kwargs={"work_id": edition.work.pk}))


class EditionUpdateView(CatalogMutationView, UpdateView):
    """Edit one edition through a thin manager-backed form view."""

    form_class = EditionForm
    page_title = "Edit edition"
    pk_url_kwarg = "edition_id"
    submit_label = "Save edition"
    context_object_name = "edition"

    def get_queryset(self) -> Any:
        """Return the active edition queryset used for lookups."""

        return selectors.edition_list()

    def get_back_url_kwargs(self) -> dict[str, Any]:
        """Return the back link for the bound edition's work."""

        edition = getattr(self, "object")
        return {"work_id": edition.work.pk}

    def form_valid(self, form: EditionForm) -> Any:
        """Persist the edition update and redirect to the parent work detail page."""

        edition = form.apply(actor=self.request.user)
        return HttpResponseRedirect(reverse("catalog-detail", kwargs={"work_id": edition.work.pk}))


class EditionArchiveView(CatalogMutationView, View):
    """Archive one edition via a protected POST action."""

    def post(self, request: Any, edition_id: int, *args: object, **kwargs: object) -> Any:
        """Archive the edition and return to the parent work detail page."""

        edition = selectors.edition_detail(edition_id)
        work = edition.work
        BookEdition.objects.archive_edition(actor=request.user, edition=edition)
        return HttpResponseRedirect(reverse("catalog-detail", kwargs={"work_id": work.pk}))
