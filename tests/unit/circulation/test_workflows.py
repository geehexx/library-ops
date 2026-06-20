"""Tests for circulation checkout and return workflow views."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.urls import reverse
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    MemberUserFactory,
    WorkContributorFactory,
    build_isbn13,
)

from libraryops.circulation.forms import CheckoutForm
from libraryops.circulation.models import Loan
from libraryops.circulation.views import CirculationWorkflowView
from libraryops.inventory.models import BookCopyStatus


class CirculationWorkflowViewTests(TestCase):
    """Cover the checkout and return workflow pages."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed a minimal circulation graph for the workflow tests."""

        call_command("seed_roles")
        cls.librarian = LibrarianUserFactory(first_name="Grace", last_name="Hopper")
        cls.member = MemberUserFactory(first_name="Ada", last_name="Lovelace")
        work_contributor = WorkContributorFactory(
            work__title="The Dispossessed",
            contributor__name="Ursula K. Le Guin",
        )
        edition = BookEditionFactory(work=work_contributor.work, isbn=build_isbn13(812))
        cls.checkout_copy = BookCopyFactory(edition=edition, barcode="BC-WF-001")
        cls.return_copy = BookCopyFactory(edition=edition, barcode="BC-WF-002")
        cls.unavailable_checkout_copy = BookCopyFactory(
            edition=edition,
            barcode="BC-WF-003",
        )
        cls.unavailable_checkout_copy.status = BookCopyStatus.ON_LOAN.value
        cls.unavailable_checkout_copy.save(update_fields=["status", "updated_at"])

    def test_checkout_workflow_renders_for_librarians(self) -> None:
        """Checkout workflow should render search controls and select lists."""

        self.client.force_login(self.librarian)

        response = self.client.get(reverse("loan-checkout"))

        assert response.status_code == 200
        self.assertContains(response, "Checkout copy")
        self.assertContains(response, "Copy")
        self.assertContains(response, "Borrower")
        self.assertContains(response, "Search copies")
        self.assertContains(response, "Search borrowers")
        self.assertContains(response, 'name="copy_query"')
        self.assertContains(response, 'name="borrower_query"')
        self.assertContains(response, 'name="copy"')
        self.assertContains(response, 'name="borrower"')
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'aria-modal="true"')
        self.assertContains(response, 'aria-describedby="workflow-description workflow-guidance"')
        self.assertContains(response, 'id="workflow-description"')
        self.assertContains(response, 'id="workflow-guidance"')
        self.assertContains(response, 'autofocus="autofocus"')
        self.assertContains(response, "Search first, then choose from the filtered select lists")
        self.assertContains(response, self.checkout_copy.barcode)
        self.assertContains(response, "Ada Lovelace")
        self.assertContains(response, f"PATRON-{self.member.pk:04d}")
        self.assertNotContains(response, "<datalist")

    def test_checkout_workflow_filters_select_options_from_search_queries(self) -> None:
        """Search terms should narrow the copy and borrower select options."""

        self.client.force_login(self.librarian)

        response = self.client.get(
            reverse("loan-checkout"),
            data={
                "copy_query": "BC-WF-001",
                "borrower_query": f"PATRON-{self.member.pk:04d}",
            },
        )

        assert response.status_code == 200
        self.assertContains(response, 'value="BC-WF-001"')
        self.assertContains(response, 'value="PATRON-')
        self.assertContains(response, self.checkout_copy.barcode)
        self.assertContains(response, "The Dispossessed")
        self.assertNotContains(response, self.return_copy.barcode)
        self.assertNotContains(response, "<datalist")

    def test_autocomplete_widget_renders_datalist_markup(self) -> None:
        """Autocomplete widgets should keep the datalist markup intact."""

        form = CheckoutForm()
        widget = form.fields["copy"].widget
        widget.options = ["BC-WF-001 · The Dispossessed"]

        rendered = widget.render("copy", "BC-WF-001")

        assert 'list="checkout-copy-options"' in rendered
        assert '<datalist id="checkout-copy-options">' in rendered
        assert '<option value="BC-WF-001 · The Dispossessed"></option>' in rendered

    def test_checkout_workflow_renders_as_an_htmx_fragment(self) -> None:
        """Checkout workflow should swap in the fragment when loaded through HTMX."""

        self.client.force_login(self.librarian)

        response = self.client.get(reverse("loan-checkout"), HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        self.assertTemplateUsed(response, "circulation/_workflow_form.html")
        self.assertContains(response, "Checkout copy")
        self.assertContains(response, 'aria-modal="true"')

    def test_workflow_template_names_require_a_template_configuration(self) -> None:
        """Workflow views should fail fast when the page template is missing."""

        request = RequestFactory().get("/")
        view = type(
            "MissingTemplateWorkflowView",
            (CirculationWorkflowView,),
            {"template_name": None},
        )()
        view.request = request

        with pytest.raises(ImproperlyConfigured):
            view.get_template_names()

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
        """Return workflow should render a searchable active-loan select."""

        self.client.force_login(self.librarian)
        Loan.objects.checkout_copy(
            actor=self.librarian, copy=self.return_copy, borrower=self.member
        )

        response = self.client.get(
            reverse("loan-return"),
            data={"loan_query": f"PATRON-{self.member.pk:04d}"},
        )

        assert response.status_code == 200
        self.assertContains(response, "Return copy")
        self.assertContains(response, "Loan")
        self.assertContains(response, "Search loans")
        self.assertContains(response, 'name="loan_query"')
        self.assertContains(response, 'name="loan"')
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'aria-modal="true"')
        self.assertContains(response, 'aria-describedby="workflow-description workflow-guidance"')
        self.assertContains(response, "Search first, then choose from the filtered select lists")
        self.assertContains(response, self.return_copy.barcode)
        self.assertContains(response, "Ada Lovelace (")
        self.assertNotContains(response, "<datalist")

    def test_return_workflow_renders_as_an_htmx_fragment(self) -> None:
        """Return workflow should swap in the fragment when loaded through HTMX."""

        self.client.force_login(self.librarian)
        Loan.objects.checkout_copy(
            actor=self.librarian, copy=self.return_copy, borrower=self.member
        )

        response = self.client.get(reverse("loan-return"), HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        self.assertTemplateUsed(response, "circulation/_workflow_form.html")
        self.assertContains(response, "Return copy")
        self.assertContains(response, 'aria-modal="true"')

    def test_return_workflow_closes_the_active_loan(self) -> None:
        """Submitting the return form should close the loan and restore availability."""

        self.client.force_login(self.librarian)
        loan = Loan.objects.checkout_copy(
            actor=self.librarian, copy=self.return_copy, borrower=self.member
        )

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
        loan = Loan.objects.checkout_copy(
            actor=self.librarian, copy=self.return_copy, borrower=self.member
        )

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
