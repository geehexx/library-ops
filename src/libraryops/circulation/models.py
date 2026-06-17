"""Circulation models for loan invariants."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


def default_due_at() -> datetime:
    """Return the default due date for a new loan."""
    return timezone.now() + timedelta(days=14)


class Loan(models.Model):
    """Represent a borrow/return event for one copy and borrower."""

    copy: models.ForeignKey[models.Model, models.Model] = models.ForeignKey(
        "inventory.BookCopy", on_delete=models.PROTECT, related_name="loans"
    )
    borrower: models.ForeignKey[models.Model, models.Model] = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loans",
    )
    checked_out_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        default=timezone.now
    )
    due_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(default=default_due_at)
    returned_at: models.DateTimeField[datetime | None, datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
    )
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Default ordering and uniqueness for active loans."""

        ordering = ("-checked_out_at",)
        constraints = (
            models.UniqueConstraint(
                fields=["copy"],
                condition=Q(returned_at__isnull=True),
                name="unique_active_loan_per_copy",
            ),
        )

    def __str__(self) -> str:
        """Return a human-readable loan label."""
        return f"{self.copy} -> {self.borrower}"

    @property
    def is_active(self) -> bool:
        """Return whether the loan is still open."""

        return self.returned_at is None
