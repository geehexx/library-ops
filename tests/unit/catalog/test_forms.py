"""Tests for catalog manager-backed forms."""

from __future__ import annotations

from io import BytesIO

from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from tests.factories import (
    BibliographicWorkFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    build_isbn13,
)

from libraryops.audit.models import AuditEvent
from libraryops.catalog.forms import CopyForm, EditionForm, WorkForm
from libraryops.inventory.models import BookCopyStatus


def _cover_upload(filename: str, format_name: str = "PNG") -> SimpleUploadedFile:
    """Build one valid in-memory cover upload."""

    buffer = BytesIO()
    Image.new("RGB", (8, 8), color=(48, 72, 144)).save(buffer, format=format_name)
    return SimpleUploadedFile(
        filename,
        buffer.getvalue(),
        content_type=f"image/{format_name.lower()}",
    )


class WorkFormTests(TestCase):
    """Cover work form validation and manager-backed persistence."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed permissions and the librarian actor."""

        call_command("seed_roles")
        cls.actor = LibrarianUserFactory()

    def test_work_form_requires_title(self) -> None:
        """Blank titles should fail validation."""

        form = WorkForm(data={"title": "", "description": "Desc"})

        assert not form.is_valid()
        assert "title" in form.errors

    def test_work_form_apply_create_update_and_archive(self) -> None:
        """The form should persist through the owning work manager."""

        initial_audit_count = AuditEvent.objects.count()
        form = WorkForm(data={"title": "Neuromancer", "description": "Cyberpunk"})
        assert form.is_valid()

        work = form.apply(actor=self.actor)
        assert work.title == "Neuromancer"
        assert AuditEvent.objects.count() == initial_audit_count + 1

        update_form = WorkForm(
            instance=work,
            data={"title": "Neuromancer (Updated)", "description": "Updated cyberpunk"},
        )
        assert update_form.is_valid()

        updated = update_form.apply(actor=self.actor)
        assert updated.title == "Neuromancer (Updated)"
        assert updated.description == "Updated cyberpunk"
        assert AuditEvent.objects.count() == initial_audit_count + 2

        archived = update_form.archive(actor=self.actor)
        assert archived.archived_at is not None
        assert AuditEvent.objects.count() == initial_audit_count + 3


class EditionFormTests(TestCase):
    """Cover edition form validation and manager-backed persistence."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed permissions and the related catalog objects."""

        call_command("seed_roles")
        cls.actor = LibrarianUserFactory()
        cls.work = BibliographicWorkFactory(title="Foundation")

    def test_edition_form_requires_work(self) -> None:
        """Blank work selections should fail validation."""

        form = EditionForm(
            data={
                "work": "",
                "publisher": "Vintage",
                "publication_year": "1995",
                "language": "en",
                "isbn": "",
                "cover_url": "",
                "description": "",
                "external_identifiers": "",
            }
        )

        assert not form.is_valid()
        assert "work" in form.errors

    def test_edition_form_persists_normalized_isbn_and_archives(self) -> None:
        """The form should persist through the owning edition manager."""

        form = EditionForm(
            data={
                "work": self.work.pk,
                "publisher": "Vintage",
                "publication_year": "1995",
                "language": "en",
                "isbn": "0-7432-7356-7",
                "cover_url": "https://example.com/foundation.jpg",
                "description": "Classic edition",
                "external_identifiers": "{}",
            },
            files={"cover_image": _cover_upload("foundation.png")},
        )
        assert form.is_valid()

        edition = form.apply(actor=self.actor)
        assert edition.isbn == "9780743273565"
        assert edition.cover_url == "https://example.com/foundation.jpg"
        assert edition.cover_image.name

        update_form = EditionForm(
            instance=edition,
            data={
                "work": self.work.pk,
                "publisher": "Vintage Classics",
                "publication_year": "1996",
                "language": "fr",
                "isbn": build_isbn13(905),
                "cover_url": "https://example.com/foundation-updated.jpg",
                "description": "Updated edition",
                "external_identifiers": "{}",
            },
        )
        assert update_form.is_valid()

        updated = update_form.apply(actor=self.actor)
        assert updated.publisher == "Vintage Classics"
        assert updated.language == "fr"
        assert updated.cover_url == "https://example.com/foundation-updated.jpg"
        assert updated.cover_image.name == edition.cover_image.name

        archived = update_form.archive(actor=self.actor)
        assert archived.archived_at is not None


class CopyFormTests(TestCase):
    """Cover copy form validation and manager-backed persistence."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed permissions and the related catalog objects."""

        call_command("seed_roles")
        cls.actor = LibrarianUserFactory()
        cls.work = BibliographicWorkFactory(title="Foundation")
        cls.edition = BookEditionFactory(work=cls.work, isbn=build_isbn13(801))

    def test_copy_form_requires_edition_and_barcode(self) -> None:
        """Blank edition and barcode inputs should fail validation."""

        form = CopyForm(
            data={
                "edition": "",
                "barcode": "",
                "status": "",
                "shelf_location": "A1",
                "condition_note": "",
            }
        )

        assert not form.is_valid()
        assert "edition" in form.errors
        assert "barcode" in form.errors

    def test_copy_form_persists_and_archives(self) -> None:
        """The form should persist through the owning copy manager."""

        form = CopyForm(
            data={
                "edition": self.edition.pk,
                "barcode": "BC-0020",
                "status": BookCopyStatus.AVAILABLE.value,
                "shelf_location": "A2",
                "condition_note": "Near mint",
            }
        )
        assert form.is_valid()

        copy = form.apply(actor=self.actor)
        assert copy.barcode == "BC-0020"
        assert copy.status == BookCopyStatus.AVAILABLE

        update_form = CopyForm(
            instance=copy,
            data={
                "edition": self.edition.pk,
                "barcode": "BC-0020",
                "status": BookCopyStatus.MAINTENANCE.value,
                "shelf_location": "B2",
                "condition_note": "Moved to reserve",
            },
        )
        assert update_form.is_valid()

        updated = update_form.apply(actor=self.actor)
        assert updated.shelf_location == "B2"
        assert updated.status == BookCopyStatus.MAINTENANCE

        archived = update_form.archive(actor=self.actor)
        assert archived.archived_at is not None
        assert archived.status == BookCopyStatus.ARCHIVED
