"""Tests for the catalog audit boundary."""

from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase
from tests.factories import BibliographicWorkFactory, LibrarianUserFactory

from libraryops.audit.models import AuditEvent


class AuditBoundaryTests(TestCase):
    """Cover the model-owned audit API."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed the role and target objects used by the boundary tests."""

        call_command("seed_roles")
        cls.actor = LibrarianUserFactory()
        cls.work = BibliographicWorkFactory(title="Boundary Work")

    def test_record_event_persists_append_only_event(self) -> None:
        """The model manager should own audit event persistence."""

        event = AuditEvent.objects.record_event(
            actor=self.actor,
            action="catalog.work.create",
            target=self.work,
            metadata={"title": self.work.title},
        )

        assert event.actor == self.actor
        assert event.action == "catalog.work.create"
        assert event.target_type == "catalog.bibliographicwork"
        assert event.target_id == self.work.pk
        assert event.target_repr == str(self.work)
        assert event.metadata == {"title": self.work.title}
