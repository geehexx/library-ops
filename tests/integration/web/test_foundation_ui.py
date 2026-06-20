"""Integration tests for the evaluator-facing foundation UI slice."""

from __future__ import annotations

from typing import Any

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    LoanFactory,
    MemberUserFactory,
    WorkContributorFactory,
    build_isbn13,
)

from libraryops.audit.models import AuditEvent
from libraryops.catalog.models import BibliographicWork, ContributorRole, ExternalSourceRecord


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

        anonymous_response: Any = self.client.get(create_url)
        assert anonymous_response.status_code == 302
        assert anonymous_response.url == f"{login_url}?next={create_url}"

        member = MemberUserFactory()
        self.client.force_login(member)
        forbidden_response = self.client.get(create_url)

        assert forbidden_response.status_code == 403
        self.assertContains(forbidden_response, "Access denied", status_code=403)
        self.assertContains(
            forbidden_response, "You do not have access to this page", status_code=403
        )
        self.assertContains(
            forbidden_response,
            (
                "Use an account with the right role, or contact an administrator "
                "if you expected access."
            ),
            status_code=403,
        )
        self.assertContains(forbidden_response, reverse("home"), status_code=403)


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

        work: Any = BibliographicWork.objects.get(title="The Left Hand of Darkness")
        edition = work.editions.get()
        copy = edition.copies.get()

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


class FoundationCatalogSearchTests(TestCase):
    """Cover the query-param search flow on the catalog index."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed one exact identifier hit and one title-text distractor."""

        cls.exact_work = WorkContributorFactory(
            work__title="Exact Search Work",
            contributor__name="Exact Search Author",
        ).work
        cls.exact_edition = BookEditionFactory(
            work=cls.exact_work,
            isbn="9780141439518",
            language="en",
            external_identifiers={
                "openlibrary_work_id": "OL1W",
                "subjects": ["Classics"],
            },
        )
        BookCopyFactory(edition=cls.exact_edition, barcode="BC-1001")
        ExternalSourceRecord.objects.create(
            source_name="openlibrary",
            source_identifier="OL1W",
            source_url="https://openlibrary.org/works/OL1W",
            work=cls.exact_work,
        )

        cls.title_work = WorkContributorFactory(
            work__title="Reference 9780141439518 BC-1001 OL1W",
            contributor__name="Reference Author",
        ).work
        cls.title_edition = BookEditionFactory(
            work=cls.title_work,
            isbn=build_isbn13(2),
            language="fr",
            external_identifiers={"subjects": ["History"]},
        )
        cls.title_copy = BookCopyFactory(edition=cls.title_edition, barcode="BC-2001")
        LoanFactory(copy=cls.title_copy)
        ExternalSourceRecord.objects.create(
            source_name="gutenberg",
            source_identifier="2001",
            source_url="https://www.gutenberg.org/ebooks/2001",
            edition=cls.title_edition,
        )

    def test_catalog_index_q_parameter_ranks_exact_identifier_first(self) -> None:
        """The index should accept q and keep exact identifier hits ahead of title text."""

        response = self.client.get(reverse("catalog-index"), data={"q": "9780141439518"})

        assert response.status_code == 200
        works = list(response.context["works"])
        assert works[0].pk == self.exact_work.pk
        assert self.title_work.pk in [work.pk for work in works]
        self.assertContains(response, 'name="q"', status_code=200)
        self.assertContains(response, 'value="9780141439518"', status_code=200)
        self.assertContains(
            response,
            'role="status" aria-live="polite"',
            status_code=200,
        )
        self.assertContains(
            response,
            'Showing 2 results for "9780141439518"',
            status_code=200,
        )
        self.assertContains(response, "Exact identifier hit", status_code=200)
        self.assertContains(response, "Matched identifier: 9780141439518", status_code=200)
        self.assertContains(response, "Availability: Available", status_code=200)
        self.assertContains(response, "Match: Exact identifier match", status_code=200)

    def test_catalog_index_facets_filter_result_set_and_render_controls(self) -> None:
        """The index should filter by the selected facets and preserve the form state."""

        response = self.client.get(
            reverse("catalog-index"),
            data={
                "availability": "available",
                "contributor": "Exact Search Author",
                "subject": "Classics",
                "language": "en",
                "source": "openlibrary",
            },
        )

        assert response.status_code == 200
        works = list(response.context["works"])
        assert [work.pk for work in works] == [self.exact_work.pk]
        self.assertContains(
            response,
            'role="status" aria-live="polite"',
            status_code=200,
        )
        self.assertContains(response, "Showing 1 result", status_code=200)
        self.assertContains(response, 'name="availability"', status_code=200)
        self.assertContains(response, 'name="contributor"', status_code=200)
        self.assertContains(response, 'name="subject"', status_code=200)
        self.assertContains(response, 'name="language"', status_code=200)
        self.assertContains(response, 'name="source"', status_code=200)
        self.assertContains(response, 'value="available" selected', status_code=200)
        self.assertContains(response, 'value="Exact Search Author" selected', status_code=200)
        self.assertContains(response, 'value="Classics" selected', status_code=200)
        self.assertContains(response, 'value="en" selected', status_code=200)
        self.assertContains(response, 'value="openlibrary" selected', status_code=200)
