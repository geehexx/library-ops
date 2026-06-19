"""Circulation manager helpers and write orchestration."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.utils import timezone

from libraryops.audit.models import AuditEvent
from libraryops.circulation import models as circulation_models
from libraryops.inventory.models import BookCopy, BookCopyStatus


def _require_loan_manager(actor: User) -> None:
    """Reject users that cannot manage circulation loans."""

    if not actor.is_authenticated or not actor.has_perm("circulation.change_loan"):
        raise PermissionDenied("Loan mutations require librarian or admin access.")


def _loan_checkout_metadata(loan: circulation_models.Loan) -> dict[str, object]:
    """Return the audit payload for a checkout event."""

    copy = cast(BookCopy, loan.copy)
    return {
        "loan_id": loan.pk,
        "copy_id": copy.pk,
        "borrower_id": loan.borrower.pk,
        "checked_out_at": loan.checked_out_at.isoformat(),
        "due_at": loan.due_at.isoformat(),
        "status": copy.status,
    }


def _loan_return_metadata(loan: circulation_models.Loan) -> dict[str, object]:
    """Return the audit payload for a return event."""

    copy = cast(BookCopy, loan.copy)
    returned_at = loan.returned_at
    return {
        "loan_id": loan.pk,
        "copy_id": copy.pk,
        "borrower_id": loan.borrower.pk,
        "returned_at": returned_at.isoformat() if returned_at else None,
        "status": copy.status,
    }


class LoanManager(models.Manager["circulation_models.Loan"]):
    """Own write orchestration for circulation loans."""

    @transaction.atomic
    def checkout_copy(
        self,
        *,
        actor: User,
        copy: BookCopy,
        borrower: User,
        due_at: datetime | None = None,
    ) -> circulation_models.Loan:
        """Create one active loan and mark the copy on loan."""

        _require_loan_manager(actor)
        if copy.pk is None:
            raise ValueError("Cannot mutate an unsaved copy.")
        if borrower.pk is None:
            raise ValueError("Cannot checkout to an unsaved borrower.")

        copy = BookCopy.objects.select_for_update().get(pk=copy.pk)
        if copy.archived_at is not None or copy.status != BookCopyStatus.AVAILABLE.value:
            raise ValidationError("Copy must be available before checkout.")
        if (
            self.get_queryset()
            .select_for_update()
            .filter(copy=copy, returned_at__isnull=True)
            .exists()
        ):
            raise ValidationError("Copy already has an active loan.")

        loan = self.create(
            copy=copy,
            borrower=borrower,
            due_at=due_at or circulation_models.default_due_at(),
        )
        copy.status = BookCopyStatus.ON_LOAN.value
        copy.save(update_fields=["status", "updated_at"])
        AuditEvent.objects.record_event(
            actor=actor,
            action="circulation.loan.checkout",
            target=loan,
            metadata=_loan_checkout_metadata(loan),
        )
        return loan

    @transaction.atomic
    def return_copy(
        self,
        *,
        actor: User,
        loan: circulation_models.Loan,
    ) -> circulation_models.Loan:
        """Close one active loan and restore the copy to available."""

        _require_loan_manager(actor)
        if loan.pk is None:
            raise ValueError("Cannot mutate an unsaved loan.")

        loan = (
            self.get_queryset()
            .select_for_update()
            .select_related("copy", "borrower")
            .get(pk=loan.pk)
        )
        if loan.returned_at is not None:
            raise ValidationError("Loan is already closed.")

        returned_at = timezone.now()
        loan.returned_at = returned_at
        loan.save(update_fields=["returned_at"])

        copy = cast(BookCopy, loan.copy)
        copy.status = BookCopyStatus.AVAILABLE.value
        copy.save(update_fields=["status", "updated_at"])

        AuditEvent.objects.record_event(
            actor=actor,
            action="circulation.loan.return",
            target=loan,
            metadata=_loan_return_metadata(loan),
        )
        return loan
