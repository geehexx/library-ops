"""Integration tests for the public-domain catalog import command."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from libraryops.catalog.management.commands.import_public_domain_catalog import (
    ImportedPublicDomainRecord,
    SOURCE_GUTENBERG,
    SOURCE_OPENLIBRARY,
)
from libraryops.catalog.models import BibliographicWork, BookEdition, ExternalSourceRecord


def _openlibrary_record() -> ImportedPublicDomainRecord:
    """Return one fixture-sized Open Library import record."""

    return ImportedPublicDomainRecord(
        source_identifier="OL-TEST-1",
        title="Pride and Prejudice",
        source_url="https://openlibrary.org/works/OL-TEST-1",
        license_note="Open Library demo fixture.",
        contributors=("Jane Austen",),
        description="Open Library fixture description.",
        publisher="Open Library Press",
        publication_year=1843,
        language="en",
        isbn="9780141439563",
        subjects=("Mathematics", "Biographies"),
        external_identifiers={"openlibrary_work_id": "OL-TEST-1"},
    )


def _gutenberg_record() -> ImportedPublicDomainRecord:
    """Return one fixture-sized Project Gutenberg import record."""

    return ImportedPublicDomainRecord(
        source_identifier="GUT-TEST-1",
        title="Pride and Prejudice",
        source_url="https://www.gutenberg.org/ebooks/GUT-TEST-1",
        license_note="Project Gutenberg demo fixture.",
        contributors=("Jane Austen",),
        description="Project Gutenberg fixture description.",
        publisher="Project Gutenberg",
        publication_year=1859,
        language="en",
        isbn="9780486415864",
        subjects=("Classics", "Fiction"),
        external_identifiers={"gutenberg_ebook_id": "GUT-TEST-1"},
    )


def _patched_loader(records: list[ImportedPublicDomainRecord]):
    """Return a loader helper that ignores the requested limit."""

    def _loader(limit: int) -> list[ImportedPublicDomainRecord]:
        return records[:limit]

    return _loader


class ImportPublicDomainCatalogCommandTests(TestCase):
    """Cover the minimal public-domain import command contract."""

    def test_dry_run_does_not_write_records(self) -> None:
        """Dry runs should leave the catalog completely untouched."""

        with patch(
            "libraryops.catalog.management.commands.import_public_domain_catalog.load_openlibrary_records",
            _patched_loader([_openlibrary_record()]),
        ):
            call_command(
                "import_public_domain_catalog",
                source=SOURCE_OPENLIBRARY,
                limit=1,
                dry_run=True,
            )

        assert BibliographicWork.objects.count() == 0
        assert BookEdition.objects.count() == 0
        assert ExternalSourceRecord.objects.count() == 0

    def test_imports_openlibrary_and_gutenberg_fixture_records(self) -> None:
        """Each source should import one normalized fixture record."""

        with patch(
            "libraryops.catalog.management.commands.import_public_domain_catalog.load_openlibrary_records",
            _patched_loader([_openlibrary_record()]),
        ):
            call_command(
                "import_public_domain_catalog",
                source=SOURCE_OPENLIBRARY,
                limit=1,
            )

        with patch(
            "libraryops.catalog.management.commands.import_public_domain_catalog.load_gutenberg_records",
            _patched_loader([_gutenberg_record()]),
        ):
            call_command(
                "import_public_domain_catalog",
                source=SOURCE_GUTENBERG,
                limit=1,
            )

        assert BibliographicWork.objects.count() == 1
        assert BookEdition.objects.count() == 2
        assert ExternalSourceRecord.objects.count() == 2

        openlibrary_record = ExternalSourceRecord.objects.get(
            source_name=SOURCE_OPENLIBRARY,
            source_identifier="OL-TEST-1",
        )
        gutenberg_record = ExternalSourceRecord.objects.get(
            source_name=SOURCE_GUTENBERG,
            source_identifier="GUT-TEST-1",
        )
        assert openlibrary_record.edition is not None
        assert gutenberg_record.edition is not None
        assert openlibrary_record.edition.work.pk == gutenberg_record.edition.work.pk
        assert openlibrary_record.edition.external_identifiers["subjects"] == [
            "Mathematics",
            "Biographies",
        ]
        assert gutenberg_record.edition.external_identifiers["subjects"] == [
            "Classics",
            "Fiction",
        ]

    def test_same_title_but_different_primary_contributor_does_not_collapse_works(self) -> None:
        """A same-title collision with different primary authors should stay separate."""

        first = _openlibrary_record()
        second = replace(
            first,
            source_identifier="OL-TEST-2",
            source_url="https://openlibrary.org/works/OL-TEST-2",
            contributors=("Charles Dickens",),
            isbn="9780141439587",
        )

        with patch(
            "libraryops.catalog.management.commands.import_public_domain_catalog.load_openlibrary_records",
            _patched_loader([first, second]),
        ):
            call_command(
                "import_public_domain_catalog",
                source=SOURCE_OPENLIBRARY,
                limit=2,
            )

        assert BibliographicWork.objects.count() == 2
        assert BookEdition.objects.count() == 2
        assert ExternalSourceRecord.objects.count() == 2

    def test_refresh_reconciles_existing_rows_without_duplicates(self) -> None:
        """Refresh should update the existing import row in place."""

        initial_record = _openlibrary_record()
        refreshed_record = replace(
            initial_record,
            title="Open Library Fixture Updated",
            description="Updated description.",
            contributors=("Ada Lovelace", "Charles Babbage"),
            subjects=("Updated", "Subjects"),
        )

        with patch(
            "libraryops.catalog.management.commands.import_public_domain_catalog.load_openlibrary_records",
            _patched_loader([initial_record]),
        ):
            call_command(
                "import_public_domain_catalog",
                source=SOURCE_OPENLIBRARY,
                limit=1,
            )

        with patch(
            "libraryops.catalog.management.commands.import_public_domain_catalog.load_openlibrary_records",
            _patched_loader([refreshed_record]),
        ):
            call_command(
                "import_public_domain_catalog",
                source=SOURCE_OPENLIBRARY,
                limit=1,
                refresh=True,
            )
            call_command(
                "import_public_domain_catalog",
                source=SOURCE_OPENLIBRARY,
                limit=1,
                refresh=True,
            )

        assert BibliographicWork.objects.count() == 1
        assert BookEdition.objects.count() == 1
        assert ExternalSourceRecord.objects.count() == 1

        work = BibliographicWork.objects.get()
        edition = BookEdition.objects.get()
        provenance = ExternalSourceRecord.objects.get()

        assert work.title == "Open Library Fixture Updated"
        assert work.description == "Updated description."
        assert edition.description == "Updated description."
        assert edition.external_identifiers["subjects"] == [
            "Updated",
            "Subjects",
        ]
        assert provenance.fetched_at is not None
        assert provenance.work is None
        assert provenance.edition is not None
        assert provenance.edition.pk == edition.pk

    def test_provenance_requires_exactly_one_target_and_stays_unique(self) -> None:
        """The provenance model should enforce the one-target rule and uniqueness."""

        work = BibliographicWork.objects.create(title="Target Work")
        edition = BookEdition.objects.create(work=work, isbn="9780141439563")

        with self.assertRaises(ValidationError):
            ExternalSourceRecord(
                source_name="openlibrary",
                source_identifier="dup-1",
                source_url="https://example.com",
                license_note="demo",
            ).full_clean()

        with self.assertRaises(ValidationError):
            ExternalSourceRecord(
                source_name="openlibrary",
                source_identifier="dup-1",
                source_url="https://example.com",
                license_note="demo",
                work=work,
                edition=edition,
            ).full_clean()

        ExternalSourceRecord.objects.create(
            source_name="openlibrary",
            source_identifier="dup-1",
            source_url="https://example.com",
            license_note="demo",
            edition=edition,
        )

        with self.assertRaises(ValidationError):
            ExternalSourceRecord(
                source_name="openlibrary",
                source_identifier="dup-1",
                source_url="https://example.com",
                license_note="demo",
                edition=edition,
            ).full_clean()
