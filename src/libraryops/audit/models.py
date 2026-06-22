"""Audit models for append-only mutation evidence."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.models import User  # noqa: TC002
from django.db import models


class AuditEventManager(models.Manager["AuditEvent"]):
    """Own append-only audit record writes."""

    def record_event(
        self,
        *,
        actor: User,
        action: str,
        target: object,
        metadata: dict[str, object] | None = None,
    ) -> AuditEvent:
        """Persist one append-only audit event."""

        if not isinstance(target, models.Model):
            raise TypeError("Audit events require a concrete Django model target.")

        return self.create(
            actor=actor if actor.is_authenticated else None,
            action=action,
            target_type=target._meta.label_lower,
            target_id=int(target.pk or 0),
            target_repr=str(target),
            metadata=metadata or {},
        )


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
    objects: ClassVar[AuditEventManager] = AuditEventManager()  # pyright: ignore[reportIncompatibleVariableOverride]

    class Meta:
        """Default ordering for audit events."""

        ordering = ("-created_at",)

    def __str__(self) -> str:
        """Return a human-readable audit label."""
        return f"{self.action} on {self.target_type}:{self.target_id}"
