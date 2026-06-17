"""Audit models for append-only mutation evidence."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Record a significant application mutation."""

    actor: models.ForeignKey[models.Model | None, models.Model | None] = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action: models.CharField[str, str] = models.CharField(max_length=128)
    target_type: models.CharField[str, str] = models.CharField(max_length=128)
    target_id: models.PositiveBigIntegerField[int, int] = models.PositiveBigIntegerField()
    target_repr: models.CharField[str, str] = models.CharField(max_length=255)
    metadata: models.JSONField[dict[str, object], dict[str, object]] = models.JSONField(
        default=dict,
        blank=True,
    )
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Default ordering for audit events."""

        ordering = ("-created_at",)

    def __str__(self) -> str:
        """Return a human-readable audit label."""
        return f"{self.action} on {self.target_type}:{self.target_id}"
