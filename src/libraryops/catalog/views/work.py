# pyright: reportMissingTypeArgument=false
"""Work views for the catalog manager slice."""

from __future__ import annotations

from typing import Any

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, UpdateView

from libraryops.catalog import selectors
from libraryops.catalog.forms import WorkForm
from libraryops.catalog.models import BibliographicWork
from libraryops.catalog.views.base import CatalogMutationView


class WorkCreateView(CatalogMutationView, FormView):
    """Create one work through a thin manager-backed form view."""

    form_class = WorkForm
    page_title = "Create work"
    submit_label = "Create work"

    def form_valid(self, form: WorkForm) -> Any:
        """Persist one work and redirect to its detail page."""

        work = form.apply(actor=self.request.user)
        return HttpResponseRedirect(reverse("catalog-detail", kwargs={"work_id": work.pk}))


class WorkUpdateView(CatalogMutationView, UpdateView):
    """Edit one work through a thin manager-backed form view."""

    form_class = WorkForm
    page_title = "Edit work"
    pk_url_kwarg = "work_id"
    submit_label = "Save work"
    context_object_name = "work"

    def get_queryset(self) -> Any:
        """Return the active work queryset used for lookups."""

        return selectors.work_list()

    def get_back_url_kwargs(self) -> dict[str, Any]:
        """Return the back link for the bound work."""

        work = getattr(self, "object")
        return {"work_id": work.pk}

    def form_valid(self, form: WorkForm) -> Any:
        """Persist the work update and redirect to the detail page."""

        work = form.apply(actor=self.request.user)
        return HttpResponseRedirect(reverse("catalog-detail", kwargs={"work_id": work.pk}))


class WorkArchiveView(CatalogMutationView, View):
    """Archive one work via a protected POST action."""

    def post(self, request: Any, work_id: int, *args: object, **kwargs: object) -> Any:
        """Archive the work and return to the index."""

        work = selectors.work_detail(work_id)
        BibliographicWork.objects.archive_work(actor=request.user, work=work)
        return HttpResponseRedirect(reverse("catalog-index"))
