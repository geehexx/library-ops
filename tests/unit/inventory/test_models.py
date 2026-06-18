"""Tests for inventory copy manager behavior."""

from __future__ import annotations

from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from tests.factories import BookEditionFactory, LibrarianUserFactory, build_isbn13

from libraryops.inventory.models import BookCopy, BookCopyStatus


class BookCopyManagerTests(TestCase):
    """Cover the copy manager's create, update, and archive behavior."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed the roles and related catalog records used by the tests."""

        call_command("seed_roles")
        cls.actor = LibrarianUserFactory()
        cls.edition = BookEditionFactory(isbn=build_isbn13(777))

    def test_create_copy_records_audit_state_and_defaults(self) -> None:
        """Creating a copy should persist defaults and emit a compact audit payload."""

        with patch("libraryops.inventory.models.record_audit_event") as record_audit_event:
            copy = BookCopy.objects.create_copy(
                actor=self.actor,
                edition=self.edition,
                barcode="BC-9000",
                shelf_location="A1",
                condition_note="",
            )

        assert copy.status == BookCopyStatus.AVAILABLE
        assert copy.archived_at is None
        record_audit_event.assert_called_once()
        assert record_audit_event.call_args.kwargs["action"] == "catalog.copy.create"
        assert record_audit_event.call_args.kwargs["metadata"] == {
            "edition_id": self.edition.pk,
            "barcode": "BC-9000",
            "status": BookCopyStatus.AVAILABLE.value,
            "shelf_location": "A1",
            "condition_note": "",
        }

    def test_update_copy_only_records_real_changes(self) -> None:
        """Updating a copy should avoid audit noise when nothing changed."""

        copy = BookCopy.objects.create_copy(
            actor=self.actor,
            edition=self.edition,
            barcode="BC-9001",
            shelf_location="A1",
            condition_note="",
        )

        with patch("libraryops.inventory.models.record_audit_event") as record_audit_event:
            unchanged = BookCopy.objects.update_copy(actor=self.actor, copy=copy)

        assert unchanged.pk == copy.pk
        record_audit_event.assert_not_called()

        with patch("libraryops.inventory.models.record_audit_event") as record_audit_event:
            updated = BookCopy.objects.update_copy(
                actor=self.actor,
                copy=copy,
                barcode="BC-9002",
                status=BookCopyStatus.MAINTENANCE,
                condition_note="Moved to reserve",
            )

        assert updated.barcode == "BC-9002"
        assert updated.status == BookCopyStatus.MAINTENANCE
        record_audit_event.assert_called_once()
        assert record_audit_event.call_args.kwargs["metadata"] == {
            "changes": {
                "barcode": {"from": "BC-9001", "to": "BC-9002"},
                "status": {
                    "from": BookCopyStatus.AVAILABLE.value,
                    "to": BookCopyStatus.MAINTENANCE.value,
                },
                "condition_note": {"from": "", "to": "Moved to reserve"},
            }
        }

    def test_archive_copy_is_idempotent(self) -> None:
        """Archiving should stamp the copy once and leave repeated calls quiet."""

        copy = BookCopy.objects.create_copy(
            actor=self.actor,
            edition=self.edition,
            barcode="BC-9003",
            shelf_location="A1",
            condition_note="",
        )

        with patch("libraryops.inventory.models.record_audit_event") as record_audit_event:
            archived = BookCopy.objects.archive_copy(actor=self.actor, copy=copy)

        assert archived.status == BookCopyStatus.ARCHIVED
        assert archived.archived_at is not None
        record_audit_event.assert_called_once()
        assert record_audit_event.call_args.kwargs["metadata"] == {
            "archived_at": archived.archived_at.isoformat(),
            "status": BookCopyStatus.ARCHIVED.value,
        }

        with patch("libraryops.inventory.models.record_audit_event") as record_audit_event:
            archived_again = BookCopy.objects.archive_copy(actor=self.actor, copy=archived)

        assert archived_again.archived_at == archived.archived_at
        record_audit_event.assert_not_called()
