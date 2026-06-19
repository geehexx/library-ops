"""Unit tests for the circulation dashboard view."""

from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
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


class LoanDashboardViewTests(TestCase):
    """Cover the role-aware loan dashboard slices."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed a small circulation graph for dashboard rendering."""

        cls.librarian = LibrarianUserFactory()
        cls.member = MemberUserFactory()
        cls.other_member = MemberUserFactory()
        work_contributor = WorkContributorFactory(
            work__title="The Left Hand of Darkness",
            contributor__name="Ursula K. Le Guin",
        )
        work = work_contributor.work
        edition = BookEditionFactory(work=work, isbn=build_isbn13(900))
        cls.active_copy = BookCopyFactory(edition=edition, barcode="BC-9001")
        cls.overdue_copy = BookCopyFactory(edition=edition, barcode="BC-9002")
        cls.returned_copy = BookCopyFactory(edition=edition, barcode="BC-9003")

        cls.active_loan = LoanFactory(
            copy=cls.active_copy,
            borrower=cls.member,
            due_at=timezone.now() + timedelta(days=3),
        )
        cls.overdue_loan = LoanFactory(
            copy=cls.overdue_copy,
            borrower=cls.other_member,
            due_at=timezone.now() - timedelta(days=1),
        )
        cls.returned_loan = LoanFactory(
            copy=cls.returned_copy,
            borrower=cls.other_member,
            due_at=timezone.now() - timedelta(days=2),
            returned_at=timezone.now() - timedelta(hours=2),
        )

    def test_librarian_sees_all_visible_loan_slices(self) -> None:
        """Librarians should see the full dashboard across all borrowers."""

        self.client.force_login(self.librarian)

        response = self.client.get(reverse("loan-dashboard"))

        assert response.status_code == 200
        self.assertContains(response, "Visible loans: 3")
        self.assertContains(response, "Active: 2")
        self.assertContains(response, "Overdue: 1")
        self.assertContains(response, self.active_copy.barcode)
        self.assertContains(response, self.overdue_copy.barcode)
        self.assertContains(response, self.returned_copy.barcode)
        self.assertContains(response, self.other_member.email)

    def test_member_only_sees_own_loans(self) -> None:
        """Members should only see their own loans on the dashboard."""

        self.client.force_login(self.member)

        response = self.client.get(reverse("loan-dashboard"))

        assert response.status_code == 200
        self.assertContains(response, "Visible loans: 1")
        self.assertContains(response, "Active: 1")
        self.assertContains(response, "Overdue: 0")
        self.assertContains(response, self.active_copy.barcode)
        self.assertNotContains(response, self.overdue_copy.barcode)
        self.assertNotContains(response, self.returned_copy.barcode)
        self.assertNotContains(response, self.other_member.email)
