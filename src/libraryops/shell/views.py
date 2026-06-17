"""Shell presentation views for the foundation dashboard."""

from __future__ import annotations

from django.views.generic import TemplateView

from libraryops.accounts.permissions import RoleContextMixin
from libraryops.catalog.models import BibliographicWork
from libraryops.inventory.models import BookCopy


class HomeView(RoleContextMixin, TemplateView):
    """Render the role-aware foundation dashboard."""

    template_name = "shell/home.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Expose foundation summary counts on the dashboard."""

        context = super().get_context_data(**kwargs)
        context["work_count"] = BibliographicWork.objects.count()
        context["copy_count"] = BookCopy.objects.count()
        return context
