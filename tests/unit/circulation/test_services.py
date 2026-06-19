"""Tests for circulation checkout and return services."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopyStatus
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    LoanFactory,
    MemberUserFactory,
    WorkContributorFactory,
    build_isbn13,
)


class CirculationServiceTests(TestCase):
    """Cover checkout and return orchestration."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed a small circulation graph for the service tests."""

        call_command("seed_roles")
        cls.actor = LibrarianUserFactory()
        cls.member = MemberUserFactory()
        cls.other_member = MemberUserFactory()
        work_contributor = WorkContributorFactory(
            work__title="The Dispossessed",
            contributor__name="Ursula K. Le Guin",
        )
        edition = BookEditionFactory(work=work_contributor.work, isbn=build_isbn13(811))
        cls.copy = BookCopyFactory(edition=edition, barcode="BC-SVC-001")

    def test_checkout_copy_persists_a_loan_and_marks_copy_on_loan(self) -> None:
        """Checkout should create a loan, update the copy, and emit audit metadata."""

        due_at = timezone.now() + timedelta(days=21)

        with patch("libraryops.audit.models.AuditEventManager.record_event") as record_audit_event:
            loan = Loan.objects.checkout_copy(
                actor=self.actor,
                copy=self.copy,
                borrower=self.member,
                due_at=due_at,
            )

        self.copy.refresh_from_db()
        assert loan.copy.pk == self.copy.pk
        assert loan.borrower.pk == self.member.pk
        assert loan.returned_at is None
        assert loan.due_at == due_at
        assert self.copy.status == BookCopyStatus.ON_LOAN
        record_audit_event.assert_called_once()
        assert record_audit_event.call_args.kwargs["action"] == "circulation.loan.checkout"
        assert record_audit_event.call_args.kwargs["metadata"] == {
            "loan_id": loan.pk,
            "copy_id": self.copy.pk,
            "borrower_id": self.member.pk,
            "checked_out_at": loan.checked_out_at.isoformat(),
            "due_at": due_at.isoformat(),
            "status": BookCopyStatus.ON_LOAN.value,
        }

    def test_checkout_copy_requires_authorized_actor(self) -> None:
        """Members should not be able to checkout copies."""

        with self.assertRaises(PermissionDenied):
            Loan.objects.checkout_copy(
                actor=self.member, copy=self.copy, borrower=self.other_member
            )

    def test_checkout_copy_rejects_unavailable_copy(self) -> None:
        """Checkout should fail when the copy already has an active loan."""

        LoanFactory(copy=self.copy, borrower=self.member)
        self.copy.status = BookCopyStatus.ON_LOAN.value
        self.copy.save(update_fields=["status"])

        with self.assertRaises(ValidationError):
            Loan.objects.checkout_copy(actor=self.actor, copy=self.copy, borrower=self.other_member)

    def test_return_copy_closes_loan_and_restores_copy_availability(self) -> None:
        """Return should close the loan, restore the copy, and emit audit metadata."""

        loan = Loan.objects.checkout_copy(actor=self.actor, copy=self.copy, borrower=self.member)

        with patch("libraryops.audit.models.AuditEventManager.record_event") as record_audit_event:
            returned = Loan.objects.return_copy(actor=self.actor, loan=loan)

        self.copy.refresh_from_db()
        returned.refresh_from_db()
        assert returned.returned_at is not None
        assert self.copy.status == BookCopyStatus.AVAILABLE
        record_audit_event.assert_called_once()
        assert record_audit_event.call_args.kwargs["action"] == "circulation.loan.return"
        assert record_audit_event.call_args.kwargs["metadata"] == {
            "loan_id": returned.pk,
            "copy_id": self.copy.pk,
            "borrower_id": self.member.pk,
            "returned_at": returned.returned_at.isoformat(),
            "status": BookCopyStatus.AVAILABLE.value,
        }

    def test_return_copy_rejects_closed_loans(self) -> None:
        """Closed loans should not be returned a second time."""

        loan = LoanFactory(
            copy=self.copy,
            borrower=self.member,
            returned_at=timezone.now() - timedelta(hours=1),
        )

        with self.assertRaises(ValidationError):
            Loan.objects.return_copy(actor=self.actor, loan=loan)
