"""Unit tests for remote source normalization and HTTP retry behavior."""

from __future__ import annotations

from io import StringIO
from typing import Any, cast
from unittest.mock import patch

import httpx
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from libraryops.catalog.management.commands import import_public_domain_catalog as import_command
from libraryops.catalog.management.commands.import_public_domain_catalog import (
    GUTENDEX_BOOKS_URL,
    OPENLIBRARY_SEARCH_URL,
    SOURCE_OPENLIBRARY,
    ImportedPublicDomainRecord,
    _external_identifiers,  # pyright: ignore[reportPrivateUsage]
    _JsonApiClient,  # pyright: ignore[reportPrivateUsage]
    _load_gutenberg_records,  # pyright: ignore[reportPrivateUsage]
    _load_openlibrary_records,  # pyright: ignore[reportPrivateUsage]
    _LoadOptions,  # pyright: ignore[reportPrivateUsage]
    _parse_gutendex_record,  # pyright: ignore[reportPrivateUsage]
    _parse_openlibrary_record,  # pyright: ignore[reportPrivateUsage]
    _record_work_key,  # pyright: ignore[reportPrivateUsage]
)
from libraryops.catalog.models import (
    BibliographicWork,
    BookEdition,
    Contributor,
    ExternalSourceRecord,
    WorkContributor,
)


class PublicDomainSourceParserTests(SimpleTestCase):
    """Verify source payloads normalize without database access."""

    def test_openlibrary_work_uses_nested_edition_metadata(self) -> None:
        """The work identity and representative edition should remain distinct."""

        record = _parse_openlibrary_record(
            {
                "key": "/works/OL1W",
                "title": "Pride and Prejudice",
                "author_name": ["Jane Austen"],
                "author_key": ["OL21594A"],
                "first_publish_year": 1813,
                "subject": ["Courtship", "England"],
                "first_sentence": ["A" * 500],
                "editions": {
                    "docs": [
                        {
                            "key": "/books/OL123M",
                            "publisher": ["Example Press"],
                            "publish_date": ["2003"],
                            "isbn": ["978-0-14-143951-8", "invalid"],
                            "cover_i": 123,
                            "ebook_access": "public",
                        }
                    ]
                },
            },
            language="en",
            seed=9,
            sample_offset=900,
        )

        assert record is not None
        assert record is not None
        assert record.source_identifier == "OL1W"
        assert record.contributors == ("Jane Austen",)
        assert record.publication_year == 2003
        assert record.isbn == "9780141439518"
        assert len(record.description) == 500
        assert record.cover_url.endswith("/123-L.jpg")
        assert record.external_identifiers == {
            "openlibrary_work_id": "OL1W",
            "metadata_provider": "openlibrary",
            "sample_seed": 9,
            "sample_offset": 900,
            "first_publish_year": 1813,
            "openlibrary_edition_id": "OL123M",
            "openlibrary_author_ids": ["OL21594A"],
            "ebook_access": "public",
        }

    def test_gutendex_record_does_not_invent_isbn_or_print_year(self) -> None:
        """Gutendex fields should be retained without fabricating edition data."""

        record = _parse_gutendex_record(
            {
                "id": 1342,
                "title": "Pride and Prejudice",
                "subjects": ["Courtship -- Fiction"],
                "authors": [{"name": "Austen, Jane"}],
                "summaries": ["B" * 800],
                "translators": [{"name": "Example, Translator"}],
                "bookshelves": ["Best Books Ever Listings"],
                "languages": ["en"],
                "copyright": False,
                "media_type": "Text",
                "formats": {"image/jpeg": "https://example.test/cover.jpg"},
                "download_count": 1234,
            },
            language="en",
            seed=9,
            sample_page=4,
        )

        assert record is not None
        assert record is not None
        assert record.contributors == ("Jane Austen",)
        assert record.publication_year is None
        assert record.isbn is None
        assert len(record.description) == 800
        assert record.cover_url == "https://example.test/cover.jpg"
        assert record.external_identifiers is not None
        assert record.external_identifiers["translators"] == ["Translator Example"]

    def test_gutendex_rejects_non_public_domain_result(self) -> None:
        """Only records explicitly marked copyright=false should import."""

        record = _parse_gutendex_record(
            {
                "id": 1,
                "title": "Not eligible",
                "copyright": True,
                "media_type": "Text",
            },
            language="en",
            seed=1,
            sample_page=1,
        )

        assert record is None


class PublicDomainSourceLoaderTests(SimpleTestCase):
    """Verify deterministic source pagination independently of the network."""

    def test_openlibrary_loader_requests_batched_search_results(self) -> None:
        """A small import should be satisfied by one Search API request."""

        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "docs": [
                        {
                            "key": "/works/OL2W",
                            "title": "Book",
                            "author_name": ["Writer"],
                            "first_publish_year": 1900,
                            "editions": {
                                "docs": [
                                    {
                                        "key": "/books/OL2M",
                                        "ebook_access": "public",
                                    }
                                ]
                            },
                        }
                    ]
                },
                request=request,
            )

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            api = _JsonApiClient(client, source_label="Open Library")
            records = _load_openlibrary_records(
                api,
                limit=1,
                options=_LoadOptions(seed=0, language="en"),
            )

        assert [record.source_identifier for record in records] == ["OL2W"]
        assert len(requests) == 1
        request = requests[0]
        assert str(request.url.copy_with(query=None)) == OPENLIBRARY_SEARCH_URL
        assert request.url.params["offset"] == "0"
        assert request.url.params["limit"] == "20"
        assert "ebook_access:public" in request.url.params["q"]

    def test_gutenberg_loader_reuses_page_one_when_selected(self) -> None:
        """The initial count request should also supply results for page one."""

        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "count": 1,
                    "results": [
                        {
                            "id": 1,
                            "title": "One",
                            "authors": [{"name": "Doe, Jane"}],
                            "languages": ["en"],
                            "copyright": False,
                            "media_type": "Text",
                            "subjects": [],
                            "bookshelves": [],
                            "summaries": [],
                            "translators": [],
                            "formats": {},
                        }
                    ],
                },
                request=request,
            )

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            api = _JsonApiClient(client, source_label="Gutendex")
            records = _load_gutenberg_records(
                api,
                limit=1,
                options=_LoadOptions(seed=0, language="en"),
            )

        assert records[0].contributors == ("Jane Doe",)
        assert len(requests) == 1
        request = requests[0]
        assert str(request.url.copy_with(query=None)) == GUTENDEX_BOOKS_URL
        assert request.url.params["page"] == "1"
        assert request.url.params["copyright"] == "false"


class JsonApiClientTests(SimpleTestCase):
    """Verify retry and error handling around HTTPX."""

    def test_retryable_status_is_retried_then_returned(self) -> None:
        """A transient upstream failure should not fail the command immediately."""

        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(503, request=request)
            return httpx.Response(200, json={"ok": True}, request=request)

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            api = _JsonApiClient(
                client,
                source_label="test",
                sleeper=lambda _seconds: None,
            )
            payload = api.get_object("https://example.test/data", params={})

        assert payload == {"ok": True}
        assert calls == 2

    def test_invalid_json_object_shape_is_rejected(self) -> None:
        """Source arrays should not be silently treated as valid response objects."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[{"unexpected": True}], request=request)

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            api = _JsonApiClient(client, source_label="test")
            with self.assertRaisesMessage(CommandError, "not an object"):
                api.get_object("https://example.test/data", params={})


def _make_import_record(
    *,
    source_identifier: str = "OL1W",
    title: str = "Pride and Prejudice",
    contributors: tuple[str, ...] = ("Jane Austen",),
    description: str = "A classic novel.",
    publisher: str = "Example Press",
    publication_year: int | None = 1813,
    language: str = "en",
    isbn: str | None = "9780141439518",
    cover_url: str = "https://example.test/cover.jpg",
    subjects: tuple[str, ...] = ("Courtship", "England"),
    source_url: str | None = None,
    license_note: str = "Open Library metadata; no new rights asserted.",
) -> ImportedPublicDomainRecord:
    """Build a deterministic public-domain import record for command tests."""

    return ImportedPublicDomainRecord(
        source_identifier=source_identifier,
        title=title,
        source_url=source_url or f"https://openlibrary.org/works/{source_identifier}",
        license_note=license_note,
        contributors=contributors,
        description=description,
        publisher=publisher,
        publication_year=publication_year,
        language=language,
        isbn=isbn,
        cover_url=cover_url,
        subjects=subjects,
        external_identifiers={"metadata_provider": SOURCE_OPENLIBRARY, "sample_seed": 11},
    )


class PublicDomainImportCommandTests(TestCase):
    """Cover command-level write, refresh, dry-run, and validation branches."""

    def _call_command(
        self,
        *,
        records: list[ImportedPublicDomainRecord],
        source: str = SOURCE_OPENLIBRARY,
        **options: object,
    ) -> tuple[str, str]:
        """Run the command against a patched loader and capture stdout/stderr."""

        stdout = StringIO()
        stderr = StringIO()
        loader_name = (
            "load_openlibrary_records" if source == SOURCE_OPENLIBRARY else "load_gutenberg_records"
        )
        with patch.object(import_command, loader_name, return_value=records):
            call_command(
                "import_public_domain_catalog",
                source=source,
                stdout=stdout,
                stderr=stderr,
                **options,
            )
        return stdout.getvalue(), stderr.getvalue()

    def test_command_rejects_invalid_limit_and_timeout(self) -> None:
        """Reject invalid numeric args before any loader or write path is reached."""

        with self.assertRaisesMessage(CommandError, "--limit must be between 1 and"):
            call_command("import_public_domain_catalog", source=SOURCE_OPENLIBRARY, limit=0)

        with self.assertRaisesMessage(CommandError, "--timeout must be greater than zero."):
            call_command(
                "import_public_domain_catalog",
                source=SOURCE_OPENLIBRARY,
                timeout=0,
            )

    def test_command_collapses_duplicate_loader_records_and_persists_provenance(self) -> None:
        """Duplicate source rows should collapse to one import and keep provenance intact."""

        first = _make_import_record(title="First Title")
        duplicate = _make_import_record(title="Duplicate Title")

        stdout, stderr = self._call_command(
            records=[first, duplicate],
            contact_email="catalog@example.test",
            limit=1,
        )

        assert "Imported 1 record(s) from openlibrary" in stdout
        assert stderr == ""
        assert BibliographicWork.objects.count() == 1
        assert BookEdition.objects.count() == 1
        assert Contributor.objects.count() == 1
        assert WorkContributor.objects.count() == 1
        assert ExternalSourceRecord.objects.count() == 1

        work = cast("Any", BibliographicWork.objects.get())
        edition = cast("Any", BookEdition.objects.select_related("work").get())
        provenance = cast("Any", ExternalSourceRecord.objects.select_related("edition").get())
        contributor = cast("Any", Contributor.objects.get())

        assert work.title == first.title
        assert edition.work_id == work.id
        assert edition.external_identifiers["source_name"] == SOURCE_OPENLIBRARY
        assert edition.external_identifiers["metadata_provider"] == SOURCE_OPENLIBRARY
        assert edition.external_identifiers["sample_seed"] == 11
        assert edition.external_identifiers["subjects"] == list(first.subjects)
        assert provenance.source_url == first.source_url
        assert provenance.license_note == first.license_note
        assert provenance.edition_id == edition.id
        assert contributor.name == first.contributors[0]

    def test_command_dry_run_reports_refresh_counts_without_writes(self) -> None:
        """Dry run should report reconciliation counts without mutating rows."""

        base_record = _make_import_record()
        self._call_command(records=[base_record], contact_email="catalog@example.test", limit=1)

        refreshed = _make_import_record(
            title="Pride and Prejudice: Revised",
            contributors=("Jane  Austen",),
            description="A revised description.",
            publisher="Revised Press",
            publication_year=1814,
            subjects=("Marriage",),
            source_url="https://openlibrary.org/works/OL1W?rev=2",
            license_note="Updated Open Library provenance.",
        )

        stdout, stderr = self._call_command(
            records=[refreshed],
            dry_run=True,
            refresh=True,
            limit=251,
        )

        assert "Dry run: fetched 1 valid record(s) from openlibrary" in stdout
        assert "would create 0, refresh 1, and skip 0" in stdout
        assert "No Open Library contact email configured" in stderr
        assert "Large API imports are intended for occasional demo seeding" in stderr

        work = cast("Any", BibliographicWork.objects.get())
        edition = cast("Any", BookEdition.objects.get())
        provenance = cast("Any", ExternalSourceRecord.objects.get())
        contributor = cast("Any", Contributor.objects.get())

        assert work.title == base_record.title
        assert edition.publisher == base_record.publisher
        assert provenance.source_url == base_record.source_url
        assert contributor.name == base_record.contributors[0]

    def test_command_refreshes_existing_rows_in_place(self) -> None:
        """Refresh should reconcile the existing work, edition, contributor, and provenance rows."""

        base_record = _make_import_record()
        self._call_command(records=[base_record], contact_email="catalog@example.test", limit=1)

        refreshed = _make_import_record(
            title="Pride and Prejudice: Revised",
            contributors=("Jane  Austen",),
            description="A revised description.",
            publisher="Revised Press",
            publication_year=1814,
            subjects=("Marriage",),
            source_url="https://openlibrary.org/works/OL1W?rev=2",
            license_note="Updated Open Library provenance.",
        )

        work = cast("Any", BibliographicWork.objects.get())
        edition = cast("Any", BookEdition.objects.get())
        provenance = cast("Any", ExternalSourceRecord.objects.get())
        contributor = cast("Any", Contributor.objects.get())

        stdout, stderr = self._call_command(
            records=[refreshed],
            refresh=True,
            contact_email="catalog@example.test",
            limit=1,
        )

        assert "Imported 0 record(s) from openlibrary; refreshed 1 and skipped 0" in stdout
        assert stderr == ""

        assert BibliographicWork.objects.count() == 1
        assert BookEdition.objects.count() == 1
        assert ExternalSourceRecord.objects.count() == 1
        assert WorkContributor.objects.count() == 1
        assert Contributor.objects.count() == 1

        refreshed_work = cast("Any", BibliographicWork.objects.get())
        refreshed_edition = cast("Any", BookEdition.objects.get())
        refreshed_provenance = cast("Any", ExternalSourceRecord.objects.get())
        refreshed_contributor = cast("Any", Contributor.objects.get())

        assert refreshed_work.id == work.id
        assert refreshed_edition.id == edition.id
        assert refreshed_provenance.id == provenance.id
        assert refreshed_contributor.id == contributor.id
        assert refreshed_work.title == refreshed.title
        assert refreshed_work.description == refreshed.description
        assert refreshed_edition.publisher == refreshed.publisher
        assert refreshed_edition.publication_year == refreshed.publication_year
        assert refreshed_edition.description == refreshed.description
        assert refreshed_edition.external_identifiers["subjects"] == list(refreshed.subjects)
        assert refreshed_provenance.source_url == refreshed.source_url
        assert refreshed_provenance.license_note == refreshed.license_note
        assert refreshed_contributor.name == refreshed.contributors[0]

    def test_command_skips_existing_rows_without_refresh(self) -> None:
        """A rerun without refresh should be idempotent and leave persisted rows untouched."""

        record = _make_import_record()
        self._call_command(records=[record], contact_email="catalog@example.test", limit=1)

        work = cast("Any", BibliographicWork.objects.get())
        edition = cast("Any", BookEdition.objects.get())
        provenance = cast("Any", ExternalSourceRecord.objects.get())
        contributor = cast("Any", Contributor.objects.get())

        stdout, stderr = self._call_command(
            records=[record],
            contact_email="catalog@example.test",
            limit=1,
        )

        assert "Imported 0 record(s) from openlibrary; refreshed 0 and skipped 1" in stdout
        assert stderr == ""
        assert BibliographicWork.objects.count() == 1
        assert BookEdition.objects.count() == 1
        assert ExternalSourceRecord.objects.count() == 1
        assert WorkContributor.objects.count() == 1
        assert Contributor.objects.count() == 1

        assert cast("Any", BibliographicWork.objects.get()).id == work.id
        assert cast("Any", BookEdition.objects.get()).id == edition.id
        assert cast("Any", ExternalSourceRecord.objects.get()).id == provenance.id
        assert cast("Any", Contributor.objects.get()).id == contributor.id


class PublicDomainImportHelperTests(SimpleTestCase):
    """Cover small pure helpers that underpin command reconciliation."""

    def test_record_key_uses_blank_primary_contributor_for_unattributed_titles(self) -> None:
        """The work key should still be stable when a record has no contributors."""

        record = _make_import_record(contributors=())

        assert _record_work_key(record) == ("pride and prejudice", "")

    def test_external_identifiers_omit_subjects_when_record_has_none(self) -> None:
        """The edition payload should not invent subject data."""

        record = _make_import_record(subjects=())

        assert _external_identifiers(SOURCE_OPENLIBRARY, record) == {
            "metadata_provider": SOURCE_OPENLIBRARY,
            "sample_seed": 11,
            "source_name": SOURCE_OPENLIBRARY,
        }
