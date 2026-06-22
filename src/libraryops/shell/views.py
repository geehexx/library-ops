"""Shell presentation views for the foundation dashboard."""

from __future__ import annotations

from django.views.generic import TemplateView

from libraryops.accounts.demo_state import demo_auth_ready, demo_data_ready
from libraryops.accounts.permissions import RoleContextMixin
from libraryops.catalog.models import BibliographicWork
from libraryops.inventory.models import BookCopy

README_URL = "https://github.com/geehexx/library-ops#readme"


class HomeView(RoleContextMixin, TemplateView):
    """Render the role-aware foundation dashboard."""

    template_name = "shell/home.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Expose foundation summary counts on the dashboard."""

        context = super().get_context_data(**kwargs)
        context["work_count"] = BibliographicWork.objects.count()
        context["copy_count"] = BookCopy.objects.count()
        context["demo_auth_ready"] = demo_auth_ready()
        context["demo_data_ready"] = demo_data_ready(context["work_count"], context["copy_count"])
        context["about_demo_url"] = README_URL
        return context
