"""Integration tests for the evaluator-facing foundation UI slice."""

from __future__ import annotations

from typing import Any, Protocol, cast

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    MemberUserFactory,
    WorkContributorFactory,
)

from libraryops.audit.models import AuditEvent
from libraryops.catalog.models import BibliographicWork, ContributorRole


class _BookCopyLike(Protocol):
    """Protocol for the minimal book-copy shape used in assertions."""

    barcode: str


class _BookEditionLike(Protocol):
    """Protocol for the minimal book-edition shape used in assertions."""

    isbn: str | None
    copies: Any


class _BibliographicWorkLike(Protocol):
    """Protocol for the minimal work shape used in assertions."""

    pk: int | None
    editions: Any
    work_contributors: Any


class FoundationNavigationTests(TestCase):
    """Cover role-aware navigation and the protected create entry point."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed the durable role groups required for permission-aware navigation."""

        call_command("seed_roles")

    def test_home_nav_is_public_for_anonymous(self) -> None:
        """Anonymous visitors should see login and catalog navigation."""

        response = self.client.get(reverse("home"))

        assert response.status_code == 200
        self.assertContains(response, reverse("catalog-index"))
        self.assertContains(response, reverse("account_login"))
        self.assertNotContains(response, reverse("catalog-create"))

    def test_home_nav_exposes_create_flow_for_librarian(self) -> None:
        """Catalog managers should see the protected create action."""

        librarian = LibrarianUserFactory()
        self.client.force_login(librarian)

        response = self.client.get(reverse("home"))

        assert response.status_code == 200
        self.assertContains(response, "Librarian")
        self.assertContains(response, reverse("catalog-create"))

    def test_catalog_create_is_protected(self) -> None:
        """Anonymous users should redirect and members should receive a 403 page."""

        login_url = reverse("account_login")
        create_url = reverse("catalog-create")

        anonymous_response = cast("Any", self.client.get(create_url))
        assert anonymous_response.status_code == 302
        assert anonymous_response.url == f"{login_url}?next={create_url}"

        member = MemberUserFactory()
        self.client.force_login(member)
        forbidden_response = self.client.get(create_url)

        assert forbidden_response.status_code == 403
        self.assertContains(forbidden_response, "Access denied", status_code=403)
        self.assertContains(forbidden_response, "You do not have permission", status_code=403)


class FoundationCreateFlowTests(TestCase):
    """Cover the protected create flow for evaluator-visible catalog data."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed role permissions before exercising protected catalog mutations."""

        call_command("seed_roles")

    def test_catalog_create_rejects_invalid_payload(self) -> None:
        """Librarians should see explicit field errors for invalid create requests."""

        librarian = LibrarianUserFactory()
        self.client.force_login(librarian)

        response = self.client.post(
            reverse("catalog-create"),
            data={
                "title": "",
                "contributor_name": "",
                "contributor_role": "",
                "isbn": "",
                "barcode": "",
                "publisher": "",
                "publication_year": "",
                "language": "",
                "shelf_location": "",
            },
        )

        assert response.status_code == 200
        assert BibliographicWork.objects.count() == 0
        self.assertContains(response, "Fix the highlighted fields")
        self.assertContains(response, "This field is required.")

    def test_librarian_can_create_foundation_record(self) -> None:
        """Librarians should create the work, edition, copy, and audit event atomically."""

        librarian = LibrarianUserFactory()
        self.client.force_login(librarian)

        response = self.client.post(
            reverse("catalog-create"),
            data={
                "title": "The Left Hand of Darkness",
                "contributor_name": "Ursula K. Le Guin",
                "contributor_role": ContributorRole.AUTHOR,
                "isbn": "9780143111597",
                "barcode": "BC-2001",
                "publisher": "Penguin",
                "publication_year": "1969",
                "language": "en",
                "shelf_location": "Fiction-1",
            },
        )

        work = cast(
            "_BibliographicWorkLike",
            BibliographicWork.objects.get(title="The Left Hand of Darkness"),
        )
        edition = cast("_BookEditionLike", work.editions.get())
        copy = cast("_BookCopyLike", edition.copies.get())

        assert response.status_code == 302
        self.assertRedirects(response, reverse("catalog-detail", kwargs={"work_id": work.pk}))
        assert work.work_contributors.count() == 1
        assert edition.isbn == "9780143111597"
        assert copy.barcode == "BC-2001"
        assert AuditEvent.objects.filter(
            actor=librarian,
            action="catalog.foundation.create",
            target_id=work.pk,
        ).exists()


class FoundationCatalogPagesTests(TestCase):
    """Cover catalog index/detail rendering for the foundation graph."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed one foundation graph for read-only page assertions."""

        work_contributor = WorkContributorFactory(
            work__title="Pride and Prejudice",
            contributor__name="Jane Austen",
        )
        cls.work = work_contributor.work
        edition = BookEditionFactory(
            work=cls.work,
            isbn="9780141439518",
            publisher="Penguin Classics",
            publication_year=1813,
            language="en",
        )
        BookCopyFactory(edition=edition, barcode="BC-0001", shelf_location="A1")

    def test_catalog_pages_render_foundation_data(self) -> None:
        """The catalog index and detail pages should expose the seeded foundation data."""

        index_response = self.client.get(reverse("catalog-index"))
        detail_response = self.client.get(
            reverse("catalog-detail", kwargs={"work_id": self.work.pk})
        )

        assert index_response.status_code == 200
        self.assertContains(index_response, "Pride and Prejudice", status_code=200)
        self.assertContains(index_response, "Jane Austen", status_code=200)
        self.assertContains(index_response, "1 edition", status_code=200)

        assert detail_response.status_code == 200
        self.assertContains(detail_response, "BC-0001", status_code=200)
        self.assertContains(detail_response, "9780141439518", status_code=200)
