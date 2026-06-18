"""Inventory models for borrowable copies."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from django.db import models


class BookCopyStatus(models.TextChoices):
    """Supported inventory statuses for a copy."""

    AVAILABLE = "available", "Available"
    ON_LOAN = "on_loan", "On loan"
    MAINTENANCE = "maintenance", "Maintenance"
    LOST = "lost", "Lost"
    ARCHIVED = "archived", "Archived"


class BookCopy(models.Model):
    """Represent a borrowable copy attached to an edition."""

    edition: models.ForeignKey[models.Model, models.Model] = models.ForeignKey(
        "catalog.BookEdition", on_delete=models.PROTECT, related_name="copies"
    )
    barcode: models.CharField[str, str] = models.CharField(max_length=64, unique=True)
    status: models.CharField[str, str] = models.CharField(
        max_length=32,
        choices=BookCopyStatus.choices,
        default=BookCopyStatus.AVAILABLE,
    )
    shelf_location: models.CharField[str, str] = models.CharField(max_length=64, blank=True)
    condition_note: models.TextField[str, str] = models.TextField(blank=True)
    archived_at: models.DateTimeField[datetime | None, datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
    )
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(auto_now=True)

    class Meta:
        """Default ordering for book copies."""

        ordering = ("barcode",)

    def __str__(self) -> str:
        """Return a human-readable copy label."""
        return self.barcode
