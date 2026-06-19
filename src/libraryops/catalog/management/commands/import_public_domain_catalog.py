"""Import a small public-domain catalog slice with provenance tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from libraryops.catalog.models import (
    BibliographicWork,
    BookEdition,
    Contributor,
    ContributorRole,
    ExternalSourceRecord,
    WorkContributor,
    normalize_name,
)

SOURCE_OPENLIBRARY = "openlibrary"
SOURCE_GUTENBERG = "gutenberg"


@dataclass(frozen=True, slots=True)
class ImportedPublicDomainRecord:
    """Normalize a source record into the smallest import contract."""

    source_identifier: str
    title: str
    source_url: str
    license_note: str
    contributors: tuple[str, ...] = ()
    description: str = ""
    publisher: str = ""
    publication_year: int | None = None
    language: str = "en"
    isbn: str | None = None
    subjects: tuple[str, ...] = ()
    external_identifiers: dict[str, object] | None = None


_OPENLIBRARY_FIXTURES: tuple[ImportedPublicDomainRecord, ...] = (
    ImportedPublicDomainRecord(
        source_identifier="OL1W",
        title="Pride and Prejudice",
        source_url="https://openlibrary.org/works/OL1W",
        license_note="Open Library public-domain demo record.",
        contributors=("Jane Austen",),
        description="A public-domain novel commonly used in catalog demos.",
        publisher="Open Library Demo",
        publication_year=1813,
        language="en",
        isbn="9780141439518",
        subjects=("Courtship", "England", "Classics"),
        external_identifiers={"openlibrary_work_id": "OL1W"},
    ),
)

_GUTENBERG_FIXTURES: tuple[ImportedPublicDomainRecord, ...] = (
    ImportedPublicDomainRecord(
        source_identifier="1342",
        title="Pride and Prejudice",
        source_url="https://www.gutenberg.org/ebooks/1342",
        license_note="Project Gutenberg public-domain demo record.",
        contributors=("Jane Austen",),
        description="A public-domain novel available from Project Gutenberg.",
        publisher="Project Gutenberg",
        publication_year=1813,
        language="en",
        isbn="9781503290563",
        subjects=("Courtship", "England", "Classics"),
        external_identifiers={"gutenberg_ebook_id": "1342"},
    ),
)


def load_openlibrary_records(limit: int) -> list[ImportedPublicDomainRecord]:
    """Return the curated Open Library demo slice."""

    return list(_OPENLIBRARY_FIXTURES[:limit])


def load_gutenberg_records(limit: int) -> list[ImportedPublicDomainRecord]:
    """Return the curated Project Gutenberg demo slice."""

    return list(_GUTENBERG_FIXTURES[:limit])


def _record_primary_contributor_key(record: ImportedPublicDomainRecord) -> str:
    """Return the normalized primary contributor for a source record."""

    if not record.contributors:
        return ""
    return normalize_name(record.contributors[0])


def _work_primary_contributor_key(work: BibliographicWork) -> str:
    """Return the normalized primary contributor attached to a work."""

    relation = (
        WorkContributor.objects.select_related("contributor")
        .filter(work=work)
        .order_by("sort_order", "id")
        .first()
    )
    if relation is None:
        return ""
    return relation.contributor.normalized_name


def _external_identifiers(
    source_name: str,
    record: ImportedPublicDomainRecord,
) -> dict[str, object]:
    """Build the edition-level metadata payload for a source import."""

    identifiers = dict(record.external_identifiers or {})
    identifiers["source_name"] = source_name
    if record.subjects:
        identifiers["subjects"] = list(record.subjects)
    return identifiers


def _upsert_contributors(
    *,
    work: BibliographicWork,
    contributor_names: tuple[str, ...],
    refresh: bool,
) -> None:
    """Attach contributors to one work, replacing them on refresh."""

    if refresh:
        WorkContributor.objects.filter(work=work).delete()
    for index, contributor_name in enumerate(contributor_names):
        contributor, created = Contributor.objects.get_or_create(
            normalized_name=normalize_name(contributor_name),
            defaults={"name": contributor_name},
        )
        if refresh and not created and contributor.name != contributor_name:
            contributor.name = contributor_name
            contributor.save()
        WorkContributor.objects.get_or_create(
            work=work,
            contributor=contributor,
            role=ContributorRole.AUTHOR if index == 0 else ContributorRole.OTHER,
            defaults={"sort_order": index},
        )


def _get_or_create_work(record: ImportedPublicDomainRecord, refresh: bool) -> BibliographicWork:
    """Return the shared work row for one imported record."""

    normalized_title = normalize_name(record.title)
    normalized_primary_contributor = _record_primary_contributor_key(record)
    work = None
    for candidate in BibliographicWork.objects.filter(normalized_title=normalized_title):
        if _work_primary_contributor_key(candidate) == normalized_primary_contributor:
            work = candidate
            break
    if work is None:
        work = BibliographicWork.objects.create(title=record.title, description=record.description)
        return work
    if refresh:
        work.title = record.title
        work.description = record.description
        work.save()
    return work


def _upsert_record(
    *,
    source_name: str,
    record: ImportedPublicDomainRecord,
    refresh: bool,
) -> tuple[str, bool]:
    """Create or reconcile one imported record."""

    existing = (
        ExternalSourceRecord.objects.select_related("work", "edition")
        .filter(source_name=source_name, source_identifier=record.source_identifier)
        .first()
    )
    now = timezone.now()
    if existing is not None:
        if not refresh:
            return "skipped", False
        edition = existing.edition
        if edition is None:
            raise CommandError("Existing provenance rows must still point at an edition target.")
        work = existing.work or edition.work
        work.title = record.title
        work.description = record.description
        work.save()
        _upsert_contributors(work=work, contributor_names=record.contributors, refresh=True)
        edition.work = work
        edition.publisher = record.publisher
        edition.publication_year = record.publication_year
        edition.language = record.language
        edition.isbn = record.isbn
        edition.description = record.description
        edition.external_identifiers = _external_identifiers(source_name, record)
        edition.save()
        existing.source_url = record.source_url
        existing.license_note = record.license_note
        existing.fetched_at = now
        existing.save()
        return "refreshed", False

    work = _get_or_create_work(record, refresh=refresh)
    _upsert_contributors(work=work, contributor_names=record.contributors, refresh=False)
    edition = BookEdition.objects.create(
        work=work,
        publisher=record.publisher,
        publication_year=record.publication_year,
        language=record.language,
        isbn=record.isbn,
        description=record.description,
        external_identifiers=_external_identifiers(source_name, record),
    )
    ExternalSourceRecord.objects.create(
        source_name=source_name,
        source_identifier=record.source_identifier,
        source_url=record.source_url,
        license_note=record.license_note,
        edition=edition,
        imported_at=now,
        fetched_at=now,
    )
    return "created", True


class Command(BaseCommand):
    """Import a reproducible public-domain catalog slice."""

    help = "Import a reproducible public-domain catalog slice."

    def add_arguments(self, parser: Any) -> None:
        """Register the import command flags."""

        parser.add_argument(
            "--source",
            choices=(SOURCE_OPENLIBRARY, SOURCE_GUTENBERG),
            required=True,
            help="Choose the public-domain source to import.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=1000,
            help="Limit the number of source records imported.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview the import without writing anything.",
        )
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Reconcile existing imported rows instead of skipping them.",
        )

    def handle(self, *_args: str, **options: object) -> None:
        """Import the selected public-domain source slice."""

        source = cast(str, options["source"])
        limit = cast(int, options["limit"])
        if limit <= 0:
            raise CommandError("--limit must be a positive integer.")

        loader = (
            load_openlibrary_records if source == SOURCE_OPENLIBRARY else load_gutenberg_records
        )
        records = loader(limit)

        created = 0
        refreshed = 0
        skipped = 0
        for record in records:
            if bool(options["dry_run"]):
                skipped += 1
                continue
            outcome, _ = _upsert_record(
                source_name=source,
                record=record,
                refresh=bool(options["refresh"]),
            )
            if outcome == "created":
                created += 1
            elif outcome == "refreshed":
                refreshed += 1
            else:
                skipped += 1

        if bool(options["dry_run"]):
            self.stdout.write(
                self.style.SUCCESS(f"Dry run: would import {skipped} record(s) from {source}.")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created} record(s) from {source}"
                + (f", refreshed {refreshed}." if refreshed else ".")
            )
        )
