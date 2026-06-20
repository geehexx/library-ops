"""Integration tests for the catalog manager-only UI flow."""

from __future__ import annotations

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    MemberUserFactory,
    WorkContributorFactory,
    build_isbn13,
)

from libraryops.audit.models import AuditEvent
from libraryops.catalog.models import BibliographicWork
from libraryops.inventory.models import BookCopyStatus


def _cover_upload(filename: str, format_name: str = "PNG") -> SimpleUploadedFile:
    """Build one small in-memory cover upload for the UI tests."""

    buffer = BytesIO()
    Image.new("RGB", (8, 8), color=(48, 72, 144)).save(buffer, format=format_name)
    return SimpleUploadedFile(
        filename,
        buffer.getvalue(),
        content_type=f"image/{format_name.lower()}",
    )


class CatalogManagementUiTests(TestCase):
    """Cover the new work/edition/copy form flow in the app templates."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed roles and one active foundation graph."""

        call_command("seed_roles")
        cls.librarian = LibrarianUserFactory()
        cls.member = MemberUserFactory()
        work_contributor = WorkContributorFactory(
            work__title="Pride and Prejudice",
            contributor__name="Jane Austen",
        )
        cls.work = work_contributor.work
        cls.edition = BookEditionFactory(
            work=cls.work,
            isbn=build_isbn13(701),
            publisher="Penguin Classics",
            publication_year=1813,
            language="en",
        )
        BookCopyFactory(edition=cls.edition, barcode="BC-0701", shelf_location="A1")

    def test_member_cannot_open_manager_pages(self) -> None:
        """Members should be blocked from the manager-only create page."""

        self.client.force_login(self.member)
        response = self.client.get(reverse("work-create"))

        assert response.status_code == 403
        self.assertContains(response, "Access denied", status_code=403)
        self.assertContains(response, "You do not have access to this page", status_code=403)
        self.assertContains(
            response,
            "Use an account with the right role, or contact an administrator if you expected access.",
            status_code=403,
        )
        self.assertContains(response, reverse("home"), status_code=403)

    def test_librarian_can_create_edit_and_archive_a_work(self) -> None:
        """Work mutations should flow through the template-backed forms."""

        self.client.force_login(self.librarian)
        initial_audit_count = AuditEvent.objects.count()

        create_response = self.client.post(
            reverse("work-create"),
            data={"title": "The Dispossessed", "description": "Anarchist science fiction"},
        )
        assert create_response.status_code == 302
        work = BibliographicWork.objects.get(title="The Dispossessed")
        assert AuditEvent.objects.count() == initial_audit_count + 1

        edit_response = self.client.post(
            reverse("work-edit", kwargs={"work_id": work.pk}),
            data={
                "title": "The Dispossessed (Updated)",
                "description": "Updated anarchist science fiction",
            },
        )
        assert edit_response.status_code == 302
        work.refresh_from_db()
        assert work.title == "The Dispossessed (Updated)"
        assert AuditEvent.objects.count() == initial_audit_count + 2

        archive_response = self.client.post(reverse("work-archive", kwargs={"work_id": work.pk}))
        assert archive_response.status_code == 302
        work.refresh_from_db()
        assert work.archived_at is not None
        assert AuditEvent.objects.count() == initial_audit_count + 3

        index_response = self.client.get(reverse("catalog-index"))
        detail_response = self.client.get(reverse("catalog-detail", kwargs={"work_id": work.pk}))
        assert index_response.status_code == 200
        self.assertNotContains(index_response, "The Dispossessed (Updated)")
        assert detail_response.status_code == 404

    def test_librarian_can_create_edit_and_archive_edition_and_copy(self) -> None:
        """Edition and copy mutations should stay visible through the work detail flow."""

        self.client.force_login(self.librarian)
        edition_isbn = build_isbn13(702)
        copy_barcode = "BC-0702"

        create_page = self.client.get(reverse("edition-create", kwargs={"work_id": self.work.pk}))
        assert create_page.status_code == 200
        self.assertContains(create_page, 'enctype="multipart/form-data"')

        create_edition_response = self.client.post(
            reverse("edition-create", kwargs={"work_id": self.work.pk}),
            data={
                "work": self.work.pk,
                "publisher": "Vintage",
                "publication_year": "1995",
                "language": "en",
                "isbn": edition_isbn,
                "cover_url": "https://example.com/ui-cover.jpg",
                "cover_image": _cover_upload("ui-cover.png"),
                "description": "New edition",
                "external_identifiers": "{}",
            },
        )
        assert create_edition_response.status_code == 302
        edition = self.work.editions.get(isbn=edition_isbn)
        assert edition.cover_url == "https://example.com/ui-cover.jpg"
        assert edition.cover_image.name

        create_copy_response = self.client.post(
            reverse("copy-create", kwargs={"edition_id": edition.pk}),
            data={
                "edition": edition.pk,
                "barcode": copy_barcode,
                "status": BookCopyStatus.AVAILABLE.value,
                "shelf_location": "B1",
                "condition_note": "Fresh copy",
            },
        )
        assert create_copy_response.status_code == 302
        copy = edition.copies.get(barcode=copy_barcode)

        edit_edition_response = self.client.post(
            reverse("edition-edit", kwargs={"edition_id": edition.pk}),
            data={
                "work": self.work.pk,
                "publisher": "Vintage Classics",
                "publication_year": "1996",
                "language": "fr",
                "isbn": edition_isbn,
                "cover_url": "https://example.com/ui-cover-updated.jpg",
                "description": "Updated edition",
                "external_identifiers": "{}",
            },
        )
        assert edit_edition_response.status_code == 302
        edition.refresh_from_db()
        assert edition.publisher == "Vintage Classics"
        assert edition.language == "fr"
        assert edition.cover_url == "https://example.com/ui-cover-updated.jpg"

        edit_copy_response = self.client.post(
            reverse("copy-edit", kwargs={"copy_id": copy.pk}),
            data={
                "edition": edition.pk,
                "barcode": copy_barcode,
                "status": BookCopyStatus.MAINTENANCE.value,
                "shelf_location": "B2",
                "condition_note": "Moved to reserve",
            },
        )
        assert edit_copy_response.status_code == 302
        copy.refresh_from_db()
        assert copy.shelf_location == "B2"
        assert copy.status == BookCopyStatus.MAINTENANCE

        archive_copy_response = self.client.post(
            reverse("copy-archive", kwargs={"copy_id": copy.pk})
        )
        assert archive_copy_response.status_code == 302
        copy.refresh_from_db()
        assert copy.archived_at is not None

        archive_edition_response = self.client.post(
            reverse("edition-archive", kwargs={"edition_id": edition.pk})
        )
        assert archive_edition_response.status_code == 302
        edition.refresh_from_db()
        assert edition.archived_at is not None

        detail_response = self.client.get(
            reverse("catalog-detail", kwargs={"work_id": self.work.pk})
        )
        assert detail_response.status_code == 200
        self.assertNotContains(detail_response, edition_isbn)
        self.assertNotContains(detail_response, copy_barcode)
