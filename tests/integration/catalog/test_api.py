"""Integration tests for the catalog Ninja API contract."""

from __future__ import annotations

import json
from typing import Any, cast

from django.core.management import call_command
from django.test import TestCase
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    MemberUserFactory,
    WorkContributorFactory,
    build_isbn13,
)

from libraryops.audit.models import AuditEvent
from libraryops.catalog.models import BibliographicWork, BookEdition
from libraryops.inventory.models import BookCopy, BookCopyStatus

CATALOG_API_ROOT = "/api/catalog"


def _related_id(payload: dict[str, Any], *candidate_keys: str) -> int:
    """Return one related object identifier from a serialized payload."""

    for key in candidate_keys:
        if key not in payload:
            continue
        value = payload[key]
        if isinstance(value, dict):
            related = cast("dict[str, Any]", value)
            return int(related["id"])
        return int(value)
    raise AssertionError(f"Missing one of {candidate_keys} in payload: {payload}")


class CatalogApiTests(TestCase):
    """Cover catalog API reads, authorization, validation, and mutation effects."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed one catalog graph and the role groups needed for RBAC checks."""

        call_command("seed_roles")
        work_contributor = WorkContributorFactory(
            work__title="Pride and Prejudice",
            contributor__name="Jane Austen",
        )
        cls.work = work_contributor.work
        cls.edition = BookEditionFactory(
            work=cls.work,
            isbn="9780141439518",
            publisher="Penguin Classics",
            publication_year=1813,
            language="en",
        )
        cls.copy = BookCopyFactory(
            edition=cls.edition,
            barcode="BC-0001",
            shelf_location="A1",
        )
        cls.librarian = LibrarianUserFactory()
        cls.member = MemberUserFactory()

    def _url(self, resource: str, pk: int | None = None) -> str:
        """Build one catalog API URL."""

        path = f"{CATALOG_API_ROOT}/{resource}"
        if pk is not None:
            return f"{path}/{pk}"
        return path

    def _json_request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        """Send one JSON request through the Django test client."""

        kwargs: dict[str, Any] = {"content_type": "application/json"}
        if payload is not None:
            kwargs["data"] = json.dumps(payload)
        return getattr(self.client, method)(path, **kwargs)

    def _assert_collection_item(
        self,
        payload: list[dict[str, Any]],
        object_id: int,
        **expected_fields: Any,
    ) -> dict[str, Any]:
        """Return the matching collection row after checking the core fields."""

        item = next(row for row in payload if row["id"] == object_id)
        for field_name, expected_value in expected_fields.items():
            assert item[field_name] == expected_value
        assert isinstance(item["created_at"], str)
        assert isinstance(item["updated_at"], str)
        return item

    def _assert_validation_error(self, response: Any) -> None:
        """Check the standard Ninja validation error shape."""

        assert response.status_code == 422
        payload = cast("dict[str, Any]", response.json())
        assert "detail" in payload
        assert isinstance(payload["detail"], list)
        assert payload["detail"]
        first_error = cast("dict[str, Any]", payload["detail"][0])
        assert {"loc", "msg", "type"} <= set(first_error)
        assert cast("list[Any]", first_error["loc"])[0] == "body"

    def test_read_endpoints_return_expected_json_shapes(self) -> None:
        """Read endpoints should expose stable resource shapes and status codes."""

        self.client.force_login(self.member)

        read_cases = (
            (
                "works",
                self.work.pk,
                {"title": self.work.title, "archived_at": None},
            ),
            (
                "editions",
                self.edition.pk,
                {
                    "isbn": self.edition.isbn,
                    "publisher": self.edition.publisher,
                    "publication_year": self.edition.publication_year,
                    "language": self.edition.language,
                    "archived_at": None,
                },
            ),
            (
                "copies",
                self.copy.pk,
                {
                    "barcode": self.copy.barcode,
                    "status": BookCopyStatus.AVAILABLE,
                    "shelf_location": self.copy.shelf_location,
                    "archived_at": None,
                },
            ),
        )

        for resource, object_id, expected_fields in read_cases:
            with self.subTest(resource=resource, endpoint="collection"):
                response = self.client.get(self._url(resource))
                assert response.status_code == 200
                payload = cast("list[dict[str, Any]]", response.json())
                assert isinstance(payload, list)
                assert len(payload) == 1
                self._assert_collection_item(payload, object_id, **expected_fields)

            with self.subTest(resource=resource, endpoint="detail"):
                response = self.client.get(self._url(resource, object_id))
                assert response.status_code == 200
                payload = cast("dict[str, Any]", response.json())
                assert payload["id"] == object_id
                for field_name, expected_value in expected_fields.items():
                    assert payload[field_name] == expected_value
                assert isinstance(payload["created_at"], str)
                assert isinstance(payload["updated_at"], str)

                if resource == "works":
                    editions = cast("list[dict[str, Any]]", payload["editions"])
                    assert len(editions) == 1
                    nested_edition = editions[0]
                    assert nested_edition["id"] == self.edition.pk
                    assert nested_edition["isbn"] == self.edition.isbn
                    copies = cast("list[dict[str, Any]]", nested_edition["copies"])
                    assert len(copies) == 1
                    assert copies[0]["id"] == self.copy.pk
                    assert copies[0]["barcode"] == self.copy.barcode
                elif resource == "editions":
                    assert _related_id(payload, "work", "work_id") == self.work.pk
                    copies = cast("list[dict[str, Any]]", payload["copies"])
                    assert len(copies) == 1
                    assert copies[0]["id"] == self.copy.pk
                    assert copies[0]["barcode"] == self.copy.barcode
                else:
                    assert _related_id(payload, "edition", "edition_id") == self.edition.pk

    def test_member_users_are_rejected_from_mutation_endpoints(self) -> None:
        """Non-manager users should receive authorization failures on writes."""

        self.client.force_login(self.member)

        create_work_payload = {"title": "Denied Work"}
        update_edition_payload = {
            "work": self.work.pk,
            "isbn": build_isbn13(901),
            "publisher": "Denied Press",
            "publication_year": 1991,
            "language": "en",
        }
        create_edition_payload = {
            "work": self.work.pk,
            "isbn": build_isbn13(902),
            "publisher": "Denied Press",
            "publication_year": 1992,
            "language": "en",
        }

        for method, path, payload, model in (
            ("post", self._url("works"), create_work_payload, BibliographicWork),
            ("post", self._url("editions"), create_edition_payload, BookEdition),
            ("put", self._url("editions", self.edition.pk), update_edition_payload, BookEdition),
            ("delete", self._url("copies", self.copy.pk), None, BookCopy),
        ):
            with self.subTest(method=method, path=path):
                before_count = model.objects.count()
                response = self._json_request(method, path, payload)
                assert response.status_code == 403
                assert model.objects.count() == before_count

        self.work.refresh_from_db()
        self.edition.refresh_from_db()
        self.copy.refresh_from_db()
        assert self.work.title == "Pride and Prejudice"
        assert self.work.archived_at is None
        assert self.edition.publisher == "Penguin Classics"
        assert self.edition.archived_at is None
        assert self.copy.status == BookCopyStatus.AVAILABLE
        assert self.copy.archived_at is None

    def test_invalid_payloads_return_structured_validation_errors(self) -> None:
        """Invalid create payloads should fail with the Ninja validation envelope."""

        self.client.force_login(self.librarian)

        for resource in ("works", "editions", "copies"):
            with self.subTest(resource=resource):
                response = self._json_request("post", self._url(resource), {})
                self._assert_validation_error(response)

    def test_librarian_can_create_update_and_archive_a_work(self) -> None:
        """Work mutations should persist changes, archive softly, and audit writes."""

        self.client.force_login(self.librarian)
        initial_audit_count = AuditEvent.objects.count()

        create_payload = {
            "title": "Neuromancer",
            "description": "Cyberpunk novel",
        }
        create_response = self._json_request("post", self._url("works"), create_payload)
        assert create_response.status_code == 201
        work = BibliographicWork.objects.get(title="Neuromancer")
        assert work.description == "Cyberpunk novel"
        assert AuditEvent.objects.count() == initial_audit_count + 1

        update_payload = {
            "title": "Neuromancer (Updated)",
            "description": "Updated cyberpunk novel",
        }
        update_response = self._json_request("put", self._url("works", work.pk), update_payload)
        assert update_response.status_code == 200
        work.refresh_from_db()
        assert work.title == "Neuromancer (Updated)"
        assert work.description == "Updated cyberpunk novel"
        assert AuditEvent.objects.count() == initial_audit_count + 2

        delete_response = self.client.delete(self._url("works", work.pk))
        assert delete_response.status_code == 200
        work.refresh_from_db()
        archived_at = work.archived_at
        assert work.archived_at is not None
        assert AuditEvent.objects.count() == initial_audit_count + 3

        archived_detail_response = self.client.get(self._url("works", work.pk))
        assert archived_detail_response.status_code == 404
        work.refresh_from_db()
        assert work.archived_at == archived_at

    def test_librarian_can_create_update_and_archive_an_edition(self) -> None:
        """Edition mutations should persist changes, archive softly, and audit writes."""

        self.client.force_login(self.librarian)
        initial_audit_count = AuditEvent.objects.count()

        create_isbn = build_isbn13(902)
        create_payload = {
            "work": self.work.pk,
            "isbn": create_isbn,
            "publisher": "Vintage Classics",
            "publication_year": 1995,
            "language": "en",
        }
        create_response = self._json_request("post", self._url("editions"), create_payload)
        assert create_response.status_code == 201
        edition = self.work.editions.get(isbn=create_isbn)
        assert edition.publisher == "Vintage Classics"
        assert AuditEvent.objects.count() == initial_audit_count + 1

        update_isbn = build_isbn13(903)
        update_payload = {
            "work": self.work.pk,
            "isbn": update_isbn,
            "publisher": "Vintage Classics Revised",
            "publication_year": 1996,
            "language": "fr",
        }
        update_response = self._json_request(
            "put", self._url("editions", edition.pk), update_payload
        )
        assert update_response.status_code == 200
        edition.refresh_from_db()
        assert edition.isbn == update_isbn
        assert edition.publisher == "Vintage Classics Revised"
        assert edition.language == "fr"
        assert AuditEvent.objects.count() == initial_audit_count + 2

        delete_response = self.client.delete(self._url("editions", edition.pk))
        assert delete_response.status_code == 200
        edition.refresh_from_db()
        archived_at = edition.archived_at
        assert edition.archived_at is not None
        assert AuditEvent.objects.count() == initial_audit_count + 3

        archived_detail_response = self.client.get(self._url("editions", edition.pk))
        assert archived_detail_response.status_code == 404
        edition.refresh_from_db()
        assert edition.archived_at == archived_at

    def test_librarian_can_create_update_and_archive_a_copy(self) -> None:
        """Copy mutations should preserve soft-delete semantics and audit writes."""

        self.client.force_login(self.librarian)
        initial_audit_count = AuditEvent.objects.count()

        create_payload = {
            "edition": self.edition.pk,
            "barcode": "BC-0002",
            "shelf_location": "A2",
            "condition_note": "Fine condition",
        }
        create_response = self._json_request("post", self._url("copies"), create_payload)
        assert create_response.status_code == 201
        copy = self.edition.copies.get(barcode="BC-0002")
        assert copy.status == BookCopyStatus.AVAILABLE
        assert copy.shelf_location == "A2"
        assert AuditEvent.objects.count() == initial_audit_count + 1

        update_payload = {
            "edition": self.edition.pk,
            "barcode": "BC-0002",
            "shelf_location": "B2",
            "condition_note": "Moved to reserve shelf",
            "status": BookCopyStatus.MAINTENANCE,
        }
        update_response = self._json_request("put", self._url("copies", copy.pk), update_payload)
        assert update_response.status_code == 200
        copy.refresh_from_db()
        assert copy.shelf_location == "B2"
        assert copy.condition_note == "Moved to reserve shelf"
        assert copy.status == BookCopyStatus.MAINTENANCE
        assert AuditEvent.objects.count() == initial_audit_count + 2

        delete_response = self.client.delete(self._url("copies", copy.pk))
        assert delete_response.status_code == 200
        copy.refresh_from_db()
        archived_at = copy.archived_at
        assert copy.status == BookCopyStatus.ARCHIVED
        assert copy.archived_at is not None
        assert AuditEvent.objects.count() == initial_audit_count + 3

        archived_detail_response = self.client.get(self._url("copies", copy.pk))
        assert archived_detail_response.status_code == 404
        copy.refresh_from_db()
        assert copy.archived_at == archived_at
        assert copy.status == BookCopyStatus.ARCHIVED
