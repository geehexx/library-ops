"""Circulation presentation and workflow views."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from libraryops.accounts.permissions import RoleContextMixin
from libraryops.circulation.forms import CheckoutForm, ReturnForm
from libraryops.circulation.responses import workflow_response
from libraryops.circulation.selectors import loan_dashboard_context


class LoanDashboardView(LoginRequiredMixin, RoleContextMixin, TemplateView):
    """Render the role-aware loan dashboard."""

    template_name = "circulation/loan_dashboard.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Attach the active, overdue, and recent loan slices."""

        context = super().get_context_data(**kwargs)
        role = self.get_user_role() or ""
        context.update(
            loan_dashboard_context(
                self.request.user,
                role=role,
                now=timezone.now(),
            )
        )
        context["can_manage_loans"] = bool(self.request.user.has_perm("circulation.change_loan"))
        return context


class CirculationWorkflowView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    RoleContextMixin,
    FormView,  # pyright: ignore[reportMissingTypeArgument]
):
    """Shared workflow scaffolding for circulation actions."""

    permission_required = "circulation.change_loan"
    raise_exception = True
    template_name = "circulation/workflow_form.html"
    fragment_template_name = "circulation/_workflow_form.html"
    back_label = "Back to loan dashboard"
    back_url_name = "loan-dashboard"
    page_title = ""
    submit_label = ""

    def get_template_names(self) -> list[str]:
        """Render the fragment when the view is loaded through HTMX."""

        if getattr(self.request, "htmx", False):
            return [self.fragment_template_name]
        template_name = self.template_name
        if template_name is None:
            raise ImproperlyConfigured(f"{self.__class__.__name__} requires template_name.")
        return [template_name]

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Attach the shared workflow labels and back link."""

        context = super().get_context_data(**kwargs)
        context.setdefault("page_title", self.page_title)
        context.setdefault("submit_label", self.submit_label)
        context.setdefault("back_label", self.back_label)
        context.setdefault("back_url", reverse(self.back_url_name))
        return context

    def get_initial(self) -> dict[str, object]:
        """Preserve lookup search terms across GET-driven filtering."""

        initial = super().get_initial()
        initial["copy_query"] = self.request.GET.get("copy_query", "")
        initial["borrower_query"] = self.request.GET.get("borrower_query", "")
        initial["loan_query"] = self.request.GET.get("loan_query", "")
        return initial

    def get_success_url(self) -> str:
        """Return to the dashboard after a successful workflow submission."""

        return reverse("loan-dashboard")

    def form_valid(self, form: Any) -> Any:
        """Redirect to the dashboard after a workflow succeeds."""

        _ = form
        return workflow_response(self.request, self.get_success_url())


class LoanCheckoutView(CirculationWorkflowView):
    """Create one checkout through the circulation workflow."""

    form_class = CheckoutForm
    page_title = "Checkout copy"
    submit_label = "Checkout copy"

    def form_valid(self, form: CheckoutForm) -> Any:
        """Persist the checkout and return to the dashboard."""

        form.apply(actor=self.request.user)
        return workflow_response(self.request, self.get_success_url())


class LoanReturnView(CirculationWorkflowView):
    """Close one loan through the circulation workflow."""

    form_class = ReturnForm
    page_title = "Return copy"
    submit_label = "Return copy"

    def form_valid(self, form: ReturnForm) -> Any:
        """Persist the return and return to the dashboard."""

        form.apply(actor=self.request.user)
        return workflow_response(self.request, self.get_success_url())
