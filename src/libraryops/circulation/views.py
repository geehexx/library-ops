"""Circulation presentation and workflow views."""

from __future__ import annotations

from typing import Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from libraryops.accounts.permissions import RoleContextMixin
from libraryops.accounts.roles import ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER
from libraryops.circulation.forms import CheckoutForm, ReturnForm
from libraryops.circulation.models import Loan


def _workflow_response(request: Any, redirect_url: str) -> HttpResponse:
    """Return a browser redirect or HTMX redirect for workflow submissions."""

    if getattr(request, "htmx", False):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = redirect_url
        return response
    return HttpResponseRedirect(redirect_url)


class LoanDashboardView(LoginRequiredMixin, RoleContextMixin, TemplateView):
    """Render the role-aware loan dashboard."""

    template_name = "circulation/loan_dashboard.html"

    def get_visible_loans(self) -> QuerySet[Loan]:
        """Return the loans visible to the current user."""

        loans = Loan.objects.select_related(
            "copy__edition__work",
            "borrower",
            "copy",
            "copy__edition",
        ).order_by("-checked_out_at")
        if self.get_user_role() == ROLE_MEMBER:
            return loans.filter(borrower=self.request.user)
        return loans

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Attach the active, overdue, and recent loan slices."""

        context = super().get_context_data(**kwargs)
        now = timezone.now()
        visible_loans = self.get_visible_loans()
        active_loans = visible_loans.filter(returned_at__isnull=True).order_by(
            "due_at",
            "-checked_out_at",
        )
        overdue_loans = active_loans.filter(due_at__lt=now)
        recent_returns = list(
            visible_loans.filter(returned_at__isnull=False).order_by(
                "-returned_at",
                "-checked_out_at",
            )[:5]
        )
        context.update(
            {
                "visible_loan_count": visible_loans.count(),
                "active_loans": active_loans,
                "active_loan_count": active_loans.count(),
                "overdue_loans": overdue_loans,
                "overdue_loan_count": overdue_loans.count(),
                "recent_returns": recent_returns,
                "recent_return_count": len(recent_returns),
                "can_manage_loans": bool(self.request.user.has_perm("circulation.change_loan")),
                "show_borrower_column": self.get_user_role() in (ROLE_ADMIN, ROLE_LIBRARIAN),
            }
        )
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
        return [cast("str", self.template_name)]

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Attach the shared workflow labels and back link."""

        context = super().get_context_data(**kwargs)
        context.setdefault("page_title", self.page_title)
        context.setdefault("submit_label", self.submit_label)
        context.setdefault("back_label", self.back_label)
        context.setdefault("back_url", reverse(self.back_url_name))
        return context

    def get_success_url(self) -> str:
        """Return to the dashboard after a successful workflow submission."""

        return reverse("loan-dashboard")

    def form_valid(self, form: Any) -> HttpResponse:
        """Redirect to the dashboard after a workflow succeeds."""

        _ = form
        return _workflow_response(self.request, self.get_success_url())


class LoanCheckoutView(CirculationWorkflowView):
    """Create one checkout through the circulation workflow."""

    form_class = CheckoutForm
    page_title = "Checkout copy"
    submit_label = "Checkout copy"

    def form_valid(self, form: CheckoutForm) -> HttpResponse:
        """Persist the checkout and return to the dashboard."""

        form.apply(actor=self.request.user)
        return super().form_valid(form)


class LoanReturnView(CirculationWorkflowView):
    """Close one loan through the circulation workflow."""

    form_class = ReturnForm
    page_title = "Return copy"
    submit_label = "Return copy"

    def form_valid(self, form: ReturnForm) -> HttpResponse:
        """Persist the return and return to the dashboard."""

        form.apply(actor=self.request.user)
        return super().form_valid(form)
