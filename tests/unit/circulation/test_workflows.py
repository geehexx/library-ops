"""Tests for circulation checkout and return workflow views."""

from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    MemberUserFactory,
    WorkContributorFactory,
    build_isbn13,
)

from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopyStatus


class CirculationWorkflowViewTests(TestCase):
    """Cover the checkout and return workflow pages."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed a minimal circulation graph for the workflow tests."""

        call_command("seed_roles")
        cls.librarian = LibrarianUserFactory()
        cls.member = MemberUserFactory()
        work_contributor = WorkContributorFactory(
            work__title="The Dispossessed",
            contributor__name="Ursula K. Le Guin",
        )
        edition = BookEditionFactory(work=work_contributor.work, isbn=build_isbn13(812))
        cls.checkout_copy = BookCopyFactory(edition=edition, barcode="BC-WF-001")
        cls.return_copy = BookCopyFactory(edition=edition, barcode="BC-WF-002")

    def test_checkout_workflow_renders_for_librarians(self) -> None:
        """Checkout workflow should render with borrower and copy selectors."""

        self.client.force_login(self.librarian)

        response = self.client.get(reverse("loan-checkout"))

        assert response.status_code == 200
        self.assertContains(response, "Checkout copy")
        self.assertContains(response, "Copy")
        self.assertContains(response, "Borrower")
        self.assertContains(response, self.checkout_copy.barcode)
        self.assertContains(response, self.member.email)

    def test_checkout_workflow_renders_as_an_htmx_fragment(self) -> None:
        """Checkout workflow should swap in the fragment when loaded through HTMX."""

        self.client.force_login(self.librarian)

        response = self.client.get(reverse("loan-checkout"), HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        self.assertTemplateUsed(response, "circulation/_workflow_form.html")
        self.assertContains(response, "Checkout copy")

    def test_checkout_workflow_persists_a_loan(self) -> None:
        """Submitting the checkout form should create a loan and mark the copy on loan."""

        self.client.force_login(self.librarian)

        response = self.client.post(
            reverse("loan-checkout"),
            data={
                "copy": self.checkout_copy.pk,
                "borrower": self.member.pk,
            },
        )

        assert response.status_code == 302
        assert response.headers["Location"] == reverse("loan-dashboard")

        self.checkout_copy.refresh_from_db()
        loan = Loan.objects.get(copy=self.checkout_copy)
        assert loan.borrower == self.member
        assert loan.returned_at is None
        assert self.checkout_copy.status == BookCopyStatus.ON_LOAN

    def test_checkout_workflow_returns_hx_redirect_for_htmx(self) -> None:
        """HTMX checkout submissions should redirect the client back to the dashboard."""

        self.client.force_login(self.librarian)

        response = self.client.post(
            reverse("loan-checkout"),
            data={
                "copy": self.checkout_copy.pk,
                "borrower": self.member.pk,
            },
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 204
        assert response.headers["HX-Redirect"] == reverse("loan-dashboard")

        self.checkout_copy.refresh_from_db()
        loan = Loan.objects.get(copy=self.checkout_copy)
        assert loan.borrower == self.member
        assert loan.returned_at is None
        assert self.checkout_copy.status == BookCopyStatus.ON_LOAN

    def test_return_workflow_renders_for_librarians(self) -> None:
        """Return workflow should render with the active loan selector."""

        self.client.force_login(self.librarian)
        Loan.objects.checkout_copy(actor=self.librarian, copy=self.return_copy, borrower=self.member)

        response = self.client.get(reverse("loan-return"))

        assert response.status_code == 200
        self.assertContains(response, "Return copy")
        self.assertContains(response, "Loan")
        self.assertContains(response, self.return_copy.barcode)

    def test_return_workflow_renders_as_an_htmx_fragment(self) -> None:
        """Return workflow should swap in the fragment when loaded through HTMX."""

        self.client.force_login(self.librarian)
        Loan.objects.checkout_copy(actor=self.librarian, copy=self.return_copy, borrower=self.member)

        response = self.client.get(reverse("loan-return"), HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        self.assertTemplateUsed(response, "circulation/_workflow_form.html")
        self.assertContains(response, "Return copy")

    def test_return_workflow_closes_the_active_loan(self) -> None:
        """Submitting the return form should close the loan and restore availability."""

        self.client.force_login(self.librarian)
        loan = Loan.objects.checkout_copy(actor=self.librarian, copy=self.return_copy, borrower=self.member)

        response = self.client.post(
            reverse("loan-return"),
            data={
                "loan": loan.pk,
            },
        )

        assert response.status_code == 302
        assert response.headers["Location"] == reverse("loan-dashboard")

        loan.refresh_from_db()
        self.return_copy.refresh_from_db()
        assert loan.returned_at is not None
        assert self.return_copy.status == BookCopyStatus.AVAILABLE

    def test_return_workflow_returns_hx_redirect_for_htmx(self) -> None:
        """HTMX return submissions should redirect the client back to the dashboard."""

        self.client.force_login(self.librarian)
        loan = Loan.objects.checkout_copy(actor=self.librarian, copy=self.return_copy, borrower=self.member)

        response = self.client.post(
            reverse("loan-return"),
            data={
                "loan": loan.pk,
            },
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 204
        assert response.headers["HX-Redirect"] == reverse("loan-dashboard")

        loan.refresh_from_db()
        self.return_copy.refresh_from_db()
        assert loan.returned_at is not None
        assert self.return_copy.status == BookCopyStatus.AVAILABLE

    def test_member_is_denied_from_workflow_pages(self) -> None:
        """Members should not be able to access mutation workflows."""

        self.client.force_login(self.member)

        checkout_response = self.client.get(reverse("loan-checkout"))
        return_response = self.client.get(reverse("loan-return"))

        assert checkout_response.status_code == 403
        assert return_response.status_code == 403
