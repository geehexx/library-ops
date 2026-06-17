"""Helpers for append-only audit writes."""

from __future__ import annotations

from django.contrib.auth.models import User  # noqa: TC002
from django.db import models

from libraryops.audit.models import AuditEvent


def record_audit_event(
    *,
    actor: User,
    action: str,
    target: object,
    metadata: dict[str, object] | None = None,
) -> AuditEvent:
    """Persist one append-only audit event."""

    if not isinstance(target, models.Model):
        raise TypeError("Audit events require a concrete Django model target.")

    return AuditEvent.objects.create(
        actor=actor if actor.is_authenticated else None,
        action=action,
        target_type=target._meta.label_lower,
        target_id=int(target.pk or 0),
        target_repr=str(target),
        metadata=metadata or {},
    )
