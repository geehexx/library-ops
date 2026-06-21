"""Import a small public-domain catalog slice with provenance tracking."""

from __future__ import annotations

from collections import Counter
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
    ImportedPublicDomainRecord(
        source_identifier="OL139424W",
        title="Jane Eyre",
        source_url="https://openlibrary.org/works/OL139424W",
        license_note="Open Library public-domain demo record.",
        contributors=("Charlotte Bronte",),
        description="A public-domain Gothic novel with strong circulation interest.",
        publisher="Open Library Demo",
        publication_year=1847,
        language="en",
        isbn="9780141441146",
        subjects=("Governesses", "England", "Classics"),
        external_identifiers={"openlibrary_work_id": "OL139424W"},
    ),
    ImportedPublicDomainRecord(
        source_identifier="OL450063W",
        title="Frankenstein",
        source_url="https://openlibrary.org/works/OL450063W",
        license_note="Open Library public-domain demo record.",
        contributors=("Mary Shelley",),
        description="A public-domain science-fiction classic used in discovery demos.",
        publisher="Open Library Demo",
        publication_year=1818,
        language="en",
        isbn="9780141439471",
        subjects=("Scientists", "Monsters", "Classics"),
        external_identifiers={"openlibrary_work_id": "OL450063W"},
    ),
    ImportedPublicDomainRecord(
        source_identifier="OL15237921W",
        title="The Adventures of Sherlock Holmes",
        source_url="https://openlibrary.org/works/OL15237921W",
        license_note="Open Library public-domain demo record.",
        contributors=("Arthur Conan Doyle",),
        description="Short detective fiction that broadens subject and contributor coverage.",
        publisher="Open Library Demo",
        publication_year=1892,
        language="en",
        isbn="9780140439083",
        subjects=("Detective and mystery stories", "London", "Classics"),
        external_identifiers={"openlibrary_work_id": "OL15237921W"},
    ),
    ImportedPublicDomainRecord(
        source_identifier="OL232769W",
        title="Moby-Dick",
        source_url="https://openlibrary.org/works/OL232769W",
        license_note="Open Library public-domain demo record.",
        contributors=("Herman Melville",),
        description="A long-form adventure novel that adds deeper browse variety.",
        publisher="Open Library Demo",
        publication_year=1851,
        language="en",
        isbn="9780142437247",
        subjects=("Whaling", "Adventure stories", "Classics"),
        external_identifiers={"openlibrary_work_id": "OL232769W"},
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
    ImportedPublicDomainRecord(
        source_identifier="98",
        title="A Tale of Two Cities",
        source_url="https://www.gutenberg.org/ebooks/98",
        license_note="Project Gutenberg public-domain demo record.",
        contributors=("Charles Dickens",),
        description="A public-domain historical novel that broadens author variety.",
        publisher="Project Gutenberg",
        publication_year=1859,
        language="en",
        isbn="9780486417769",
        subjects=("French Revolution", "Historical fiction", "Classics"),
        external_identifiers={"gutenberg_ebook_id": "98"},
    ),
    ImportedPublicDomainRecord(
        source_identifier="35",
        title="The Time Machine",
        source_url="https://www.gutenberg.org/ebooks/35",
        license_note="Project Gutenberg public-domain demo record.",
        contributors=("H. G. Wells",),
        description="A compact science-fiction record suited for exact and lexical search.",
        publisher="Project Gutenberg",
        publication_year=1895,
        language="en",
        isbn="9780553213515",
        subjects=("Time travel", "Science fiction", "Classics"),
        external_identifiers={"gutenberg_ebook_id": "35"},
    ),
    ImportedPublicDomainRecord(
        source_identifier="43",
        title="The Strange Case of Dr. Jekyll and Mr. Hyde",
        source_url="https://www.gutenberg.org/ebooks/43",
        license_note="Project Gutenberg public-domain demo record.",
        contributors=("Robert Louis Stevenson",),
        description="A public-domain novella that adds shorter-form catalog depth.",
        publisher="Project Gutenberg",
        publication_year=1886,
        language="en",
        isbn="9780486266886",
        subjects=("Duality", "Psychological fiction", "Classics"),
        external_identifiers={"gutenberg_ebook_id": "43"},
    ),
    ImportedPublicDomainRecord(
        source_identifier="174",
        title="The Picture of Dorian Gray",
        source_url="https://www.gutenberg.org/ebooks/174",
        license_note="Project Gutenberg public-domain demo record.",
        contributors=("Oscar Wilde",),
        description="A public-domain novel that adds Victorian and aesthetic themes.",
        publisher="Project Gutenberg",
        publication_year=1890,
        language="en",
        isbn="9780486278070",
        subjects=("Appearance", "Moral corruption", "Classics"),
        external_identifiers={"gutenberg_ebook_id": "174"},
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
        return BibliographicWork.objects.create(title=record.title, description=record.description)
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

        source = cast("str", options["source"])
        limit = cast("int", options["limit"])
        if limit <= 0:
            raise CommandError("--limit must be a positive integer.")

        loader = {
            SOURCE_OPENLIBRARY: load_openlibrary_records,
            SOURCE_GUTENBERG: load_gutenberg_records,
        }[source]
        records = loader(limit)

        if bool(options["dry_run"]):
            self.stdout.write(
                self.style.SUCCESS(f"Dry run: would import {len(records)} record(s) from {source}.")
            )
            return

        outcomes = Counter[str]()
        outcome_aliases = {"created": "created", "refreshed": "refreshed"}
        refresh = bool(options["refresh"])
        for record in records:
            outcome, _ = _upsert_record(
                source_name=source,
                record=record,
                refresh=refresh,
            )
            outcomes[outcome_aliases.get(outcome, "skipped")] += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {outcomes['created']} record(s) from {source}"
                + (f", refreshed {outcomes['refreshed']}." if outcomes["refreshed"] else ".")
            )
        )
