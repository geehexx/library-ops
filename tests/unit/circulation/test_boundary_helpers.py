"""Tests for circulation helper boundaries."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, cast

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.utils import timezone
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    LoanFactory,
    MemberUserFactory,
    WorkContributorFactory,
    build_isbn13,
)

from libraryops.accounts.roles import ROLE_LIBRARIAN, ROLE_MEMBER
from libraryops.circulation.models import Loan
from libraryops.circulation.responses import workflow_response
from libraryops.circulation.selectors import (
    checkout_borrower_queryset,
    checkout_copy_queryset,
    loan_dashboard_context,
    resolve_borrower,
    resolve_copy,
    resolve_loan,
    return_loan_queryset,
)
from libraryops.inventory.models import BookCopy, BookCopyStatus


class CirculationBoundaryHelperTests(TestCase):
    """Cover the selector and response helpers used by circulation views."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed a minimal circulation graph for the boundary helpers."""

        cls.factory = RequestFactory()
        cls.librarian = LibrarianUserFactory()
        cls.member = MemberUserFactory(first_name="Ada", last_name="Lovelace")
        cls.other_member = MemberUserFactory()
        work_contributor = WorkContributorFactory(
            work__title="The Left Hand of Darkness",
            contributor__name="Ursula K. Le Guin",
        )
        edition = BookEditionFactory(work=work_contributor.work, isbn=build_isbn13(900))
        cls.available_copy = BookCopyFactory(edition=edition, barcode="BC-9001")
        cls.unavailable_copy = BookCopyFactory(edition=edition, barcode="BC-9002")
        cls.unavailable_copy.status = BookCopyStatus.ON_LOAN.value
        cls.unavailable_copy.save(update_fields=["status", "updated_at"])
        cls.active_copy = BookCopyFactory(edition=edition, barcode="BC-9003")
        cls.active_loan = LoanFactory(
            copy=cls.active_copy,
            borrower=cls.member,
            due_at=timezone.now() + timedelta(days=3),
        )
        cls.returned_copy = BookCopyFactory(edition=edition, barcode="BC-9004")
        cls.returned_loan = LoanFactory(
            copy=cls.returned_copy,
            borrower=cls.other_member,
            due_at=timezone.now() - timedelta(days=2),
            returned_at=timezone.now() - timedelta(hours=2),
        )

    def test_selector_helpers_scope_workflow_choices(self) -> None:
        """Selectors should keep the workflow choice sets stable and scoped."""

        checkout_copies = list(checkout_copy_queryset())
        borrowers = list(checkout_borrower_queryset())
        return_loans = list(return_loan_queryset())

        assert self.available_copy in checkout_copies
        assert self.unavailable_copy not in checkout_copies
        assert self.member in borrowers
        assert self.active_loan in return_loans
        assert self.returned_loan not in return_loans

    def test_selector_resolvers_match_exact_copy_borrower_and_loan_labels(self) -> None:
        """Resolvers should keep resolving the unique copy, borrower, and loan choices."""

        copies = BookCopy.objects.all()
        users = User.objects.all()
        loans = Loan.objects.all()

        assert resolve_copy(self.available_copy.barcode, copies) == self.available_copy
        assert resolve_borrower("Ada Lovelace", users) == self.member
        assert resolve_loan(str(self.active_loan.pk), loans) == self.active_loan

    def test_dashboard_context_preserves_role_visibility(self) -> None:
        """Dashboard slices should keep member visibility narrower than staff."""

        librarian_context = loan_dashboard_context(
            self.librarian,
            role=ROLE_LIBRARIAN,
            now=timezone.now(),
        )
        member_context = loan_dashboard_context(
            self.member,
            role=ROLE_MEMBER,
            now=timezone.now(),
        )

        assert librarian_context["visible_loan_count"] == 2
        assert librarian_context["active_loan_count"] == 1
        assert librarian_context["overdue_loan_count"] == 0
        assert librarian_context["show_borrower_column"] is True
        assert member_context["visible_loan_count"] == 1
        assert member_context["active_loan_count"] == 1
        assert member_context["overdue_loan_count"] == 0
        assert member_context["show_borrower_column"] is False

    def test_workflow_response_supports_standard_and_htmx_redirects(self) -> None:
        """Workflow response selection should preserve browser behavior."""

        request = self.factory.post("/")

        standard_response = workflow_response(request, "/circulation/")
        assert standard_response.status_code == 302
        assert standard_response.headers["Location"] == "/circulation/"

        cast("Any", request).htmx = True
        htmx_response = workflow_response(request, "/circulation/")
        assert htmx_response.status_code == 204
        assert htmx_response.headers["HX-Redirect"] == "/circulation/"
