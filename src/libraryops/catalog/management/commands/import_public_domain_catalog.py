"""Import a semi-random public-domain catalog slice with provenance tracking."""

from __future__ import annotations

import math
import os
import re
import time
from collections import Counter
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar, cast
from urllib.parse import urlsplit

import httpx
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from libraryops.catalog.models import (
    BibliographicWork,
    BookEdition,
    Contributor,
    ContributorRole,
    ExternalSourceRecord,
    WorkContributor,
    clean_isbn,
    normalize_name,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence

SOURCE_OPENLIBRARY = "openlibrary"
SOURCE_GUTENBERG = "gutenberg"

OPENLIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPENLIBRARY_WORK_URL = "https://openlibrary.org/works/{identifier}"
OPENLIBRARY_COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
GUTENDEX_BOOKS_URL = "https://gutendex.com/books"
GUTENBERG_EBOOK_URL = "https://www.gutenberg.org/ebooks/{identifier}"

CONTACT_EMAIL_ENV = "LIBRARYOPS_CATALOG_CONTACT_EMAIL"
DEFAULT_LIMIT = 100
MAX_API_RECORDS = 1_000
DEFAULT_SAMPLE_SEED = 1_729
DEFAULT_TIMEOUT_SECONDS = 20.0
MAX_DESCRIPTION_LENGTH = 5_000
MAX_SUBJECTS = 40
DATABASE_QUERY_CHUNK_SIZE = 400
OPENLIBRARY_PAGE_SIZE = 100
OPENLIBRARY_SAMPLE_WINDOWS = 100
GUTENDEX_PAGE_SIZE = 32
HTTP_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
USER_AGENT_NAME = "LibraryOpsCatalogSeeder/1.0"

# Open Library's search index uses MARC/Bibliographic three-letter codes.
OPENLIBRARY_LANGUAGE_CODES: dict[str, str] = {
    "ar": "ara",
    "cs": "cze",
    "da": "dan",
    "de": "ger",
    "el": "gre",
    "en": "eng",
    "es": "spa",
    "fi": "fin",
    "fr": "fre",
    "he": "heb",
    "hi": "hin",
    "hu": "hun",
    "id": "ind",
    "it": "ita",
    "ja": "jpn",
    "ko": "kor",
    "la": "lat",
    "nl": "dut",
    "no": "nor",
    "pl": "pol",
    "pt": "por",
    "ro": "rum",
    "ru": "rus",
    "sv": "swe",
    "tr": "tur",
    "uk": "ukr",
    "vi": "vie",
    "zh": "chi",
}

OPENLIBRARY_FIELDS = ",".join(
    (
        "key",
        "title",
        "author_name",
        "author_key",
        "first_publish_year",
        "subject",
        "first_sentence",
        "cover_i",
        "editions",
        "editions.key",
        "editions.title",
        "editions.subtitle",
        "editions.publish_date",
        "editions.publisher",
        "editions.language",
        "editions.isbn",
        "editions.cover_i",
        "editions.ebook_access",
    )
)

_YEAR_PATTERN = re.compile(r"(?<!\d)([12]\d{3})(?!\d)")
_OPENLIBRARY_ID_PATTERN = re.compile(r"^OL\d+[WMA]$")
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ImportedPublicDomainRecord:
    """Normalize source metadata into the catalog import contract."""

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
    cover_url: str = ""
    subjects: tuple[str, ...] = ()
    external_identifiers: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class _LoadOptions:
    """Options shared with patchable source-loader functions."""

    seed: int = DEFAULT_SAMPLE_SEED
    language: str = "en"
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    contact_email: str = ""


@dataclass(slots=True)
class _ImportState:
    """Hold request-local ORM indexes and avoid per-record lookup queries."""

    external_records: dict[str, ExternalSourceRecord]
    works: dict[tuple[str, str], BibliographicWork]
    contributors: dict[str, Contributor]


@dataclass(frozen=True, slots=True)
class _CommandOptions:
    """Validated CLI options for one import run."""

    source: str
    limit: int
    seed: int
    language: str
    contact_email: str
    timeout_seconds: float
    refresh: bool
    dry_run: bool


_ACTIVE_LOAD_OPTIONS: ContextVar[_LoadOptions | None] = ContextVar(
    "public_domain_catalog_load_options",
    default=None,
)
_DEFAULT_LOAD_OPTIONS = _LoadOptions()


class _RateLimiter:
    """Enforce a minimum interval between requests to one upstream."""

    def __init__(
        self,
        minimum_interval_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.minimum_interval_seconds = minimum_interval_seconds
        self._clock = clock
        self._sleeper = sleeper
        self._last_request_at: float | None = None

    def wait(self) -> None:
        """Sleep only for the remaining portion of the configured interval."""

        if self._last_request_at is not None:
            elapsed = self._clock() - self._last_request_at
            remaining = self.minimum_interval_seconds - elapsed
            if remaining > 0:
                self._sleeper(remaining)
        self._last_request_at = self._clock()


class _JsonApiClient:
    """Fetch JSON objects with bounded retries and useful command errors."""

    def __init__(
        self,
        client: httpx.Client,
        *,
        source_label: str,
        rate_limiter: _RateLimiter | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._source_label = source_label
        self._rate_limiter = rate_limiter
        self._sleeper = sleeper

    def get_object(self, url: str, *, params: Mapping[str, str | int]) -> dict[str, object]:
        """Return one JSON object or raise a source-specific ``CommandError``."""

        last_error: httpx.RequestError | None = None
        for attempt in range(1, HTTP_ATTEMPTS + 1):
            try:
                response = self._request_response(url, params=params, attempt=attempt)
            except httpx.RequestError as exc:
                last_error = exc
                continue
            if response is None:
                continue
            payload = self._payload_or_retry(response, attempt=attempt)
            if payload is not None:
                return payload

        if last_error is None:
            raise CommandError(
                f"{self._source_label} could not return a JSON object after "
                f"{HTTP_ATTEMPTS} attempts."
            )
        raise CommandError(
            f"Could not reach {self._source_label} after {HTTP_ATTEMPTS} attempts: {last_error}."
        ) from last_error

    def _request_response(
        self,
        url: str,
        *,
        params: Mapping[str, str | int],
        attempt: int,
    ) -> httpx.Response | None:
        """Return a response for one attempt or ``None`` when a retry is scheduled."""

        if self._rate_limiter is not None:
            self._rate_limiter.wait()
        try:
            return self._client.get(url, params=params)
        except httpx.RequestError:
            if attempt != HTTP_ATTEMPTS:
                self._sleeper(_backoff_seconds(attempt))
            raise

    def _payload_or_retry(
        self,
        response: httpx.Response,
        *,
        attempt: int,
    ) -> dict[str, object] | None:
        """Return payload for a successful response or ``None`` for retryable status."""

        if response.status_code in RETRYABLE_STATUS_CODES:
            if attempt == HTTP_ATTEMPTS:
                raise CommandError(
                    f"{self._source_label} returned HTTP {response.status_code} "
                    f"after {HTTP_ATTEMPTS} attempts."
                )
            self._sleeper(_retry_delay_seconds(response, attempt))
            return None
        self._raise_for_status(response)
        return self._response_payload(response)

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise a source-specific command error for non-retryable HTTP failure."""

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise CommandError(
                f"{self._source_label} returned HTTP {response.status_code} for {exc.request.url}."
            ) from exc

    def _response_payload(self, response: httpx.Response) -> dict[str, object]:
        """Return one JSON-object payload for a successful HTTP response."""

        try:
            payload: object = response.json()
        except ValueError as exc:
            raise CommandError(
                f"{self._source_label} returned invalid JSON for {response.request.url}."
            ) from exc
        if not isinstance(payload, dict):
            raise CommandError(
                f"{self._source_label} returned a JSON value that was not an object."
            )
        return cast("dict[str, object]", payload)


def _backoff_seconds(attempt: int) -> float:
    """Return a small capped exponential retry delay."""

    return min(0.5 * (2 ** (attempt - 1)), 5.0)


def _retry_delay_seconds(response: httpx.Response, attempt: int) -> float:
    """Honor a simple numeric Retry-After header before using backoff."""

    retry_after = response.headers.get("Retry-After", "").strip()
    try:
        return min(max(float(retry_after), 0.0), 30.0)
    except ValueError:
        return _backoff_seconds(attempt)


def _http_client(options: _LoadOptions) -> httpx.Client:
    """Create one pooled synchronous client for a source import."""

    contact_email = options.contact_email.strip()
    user_agent = f"{USER_AGENT_NAME} ({contact_email})" if contact_email else USER_AGENT_NAME
    timeout = httpx.Timeout(
        options.timeout_seconds,
        connect=min(options.timeout_seconds, 10.0),
    )
    limits = httpx.Limits(max_connections=4, max_keepalive_connections=2)
    return httpx.Client(
        headers={"Accept": "application/json", "User-Agent": user_agent},
        timeout=timeout,
        limits=limits,
        follow_redirects=True,
    )


def _chunks[T](values: Sequence[T], size: int = DATABASE_QUERY_CHUNK_SIZE) -> Iterator[list[T]]:
    """Yield bounded chunks suitable for SQLite and PostgreSQL ``IN`` queries."""

    for start in range(0, len(values), size):
        yield list(values[start : start + size])


def _clean_text(value: object, *, max_length: int) -> str:
    """Normalize remote text and cap it to the receiving model field."""

    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:max_length].strip()


def _text_values(
    value: object,
    *,
    max_items: int | None = None,
    max_length: int = 255,
) -> list[str]:
    """Return normalized non-empty strings from a scalar or JSON array."""

    raw_values: Sequence[object]
    if isinstance(value, str):
        raw_values = (value,)
    elif isinstance(value, (list, tuple)):
        raw_values = cast("Sequence[object]", value)
    else:
        return []

    output: list[str] = []
    seen: set[str] = set()
    for raw_value in raw_values:
        text = _clean_text(raw_value, max_length=max_length)
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        output.append(text)
        if max_items is not None and len(output) >= max_items:
            break
    return output


def _first_text(value: object, *, max_length: int = 255) -> str:
    """Return the first normalized string from a scalar or JSON array."""

    values = _text_values(value, max_items=1, max_length=max_length)
    if not values:
        return ""
    return values[0][:max_length].strip()


def _object(value: object) -> dict[str, object]:
    """Return a JSON object or an empty object."""

    if not isinstance(value, dict):
        return {}
    return cast("dict[str, object]", value)


def _object_list(value: object) -> list[dict[str, object]]:
    """Return only JSON objects from a remote list."""

    if not isinstance(value, list):
        return []
    items = cast("list[object]", value)
    objects: list[dict[str, object]] = []
    for item in items:
        if isinstance(item, dict):
            objects.append(cast("dict[str, object]", item))
    return objects


def _safe_int(value: object) -> int | None:
    """Return an integer without accepting booleans as integers."""

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _year(value: object) -> int | None:
    """Extract a model-safe publication year from common API representations."""

    direct = _safe_int(value)
    current_year = timezone.now().year
    if direct is not None and 1 <= direct <= current_year:
        return direct

    for text in _text_values(value):
        match = _YEAR_PATTERN.search(text)
        if match is None:
            continue
        parsed = int(match.group(1))
        if parsed <= current_year:
            return parsed
    return None


def _valid_isbn(value: object) -> str | None:
    """Return the first valid normalized ISBN from remote candidate values."""

    for candidate in _text_values(value):
        try:
            return clean_isbn(candidate)
        except ValidationError:
            continue
    return None


def _safe_url(value: object) -> str:
    """Return an HTTP(S) URL suitable for a Django ``URLField``."""

    url = _clean_text(value, max_length=500)
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return url


def _openlibrary_identifier(value: object) -> str:
    """Normalize an Open Library key such as ``/works/OL123W``."""

    raw = _first_text(value)
    identifier = raw.strip("/").rsplit("/", maxsplit=1)[-1]
    if not _OPENLIBRARY_ID_PATTERN.fullmatch(identifier):
        return ""
    return identifier


def _person_display_name(value: object) -> str:
    """Convert Gutendex's ``Family, Given`` names into display order."""

    name = _first_text(value)
    if "," not in name:
        return name
    family_name, given_names = (part.strip() for part in name.split(",", maxsplit=1))
    if not family_name or not given_names:
        return name
    return _clean_text(f"{given_names} {family_name}", max_length=255)


def _first_openlibrary_edition(work: Mapping[str, object]) -> dict[str, object]:
    """Return the single relevance-ranked edition embedded by Search API."""

    editions = _object(work.get("editions"))
    edition_docs = _object_list(editions.get("docs"))
    return edition_docs[0] if edition_docs else {}


def _parse_openlibrary_record(
    work: Mapping[str, object],
    *,
    language: str,
    seed: int,
    sample_offset: int,
) -> ImportedPublicDomainRecord | None:
    """Convert one Open Library work/search result into the import contract."""

    work_id = _openlibrary_identifier(work.get("key"))
    title = _first_text(work.get("title"), max_length=255)
    if not work_id or not title:
        return None

    contributors = tuple(_text_values(work.get("author_name"), max_items=20))
    author_ids = [
        identifier
        for raw_key in _text_values(work.get("author_key"), max_items=20)
        if (identifier := _openlibrary_identifier(raw_key))
    ]
    subjects = tuple(_text_values(work.get("subject"), max_items=MAX_SUBJECTS))
    description = _first_text(
        work.get("first_sentence"),
        max_length=MAX_DESCRIPTION_LENGTH,
    )

    edition = _first_openlibrary_edition(work)
    edition_id = _openlibrary_identifier(edition.get("key"))
    publisher = _first_text(edition.get("publisher"), max_length=255)
    publication_year = _year(edition.get("publish_date")) or _year(work.get("first_publish_year"))
    isbn = _valid_isbn(edition.get("isbn"))
    cover_id = _safe_int(edition.get("cover_i")) or _safe_int(work.get("cover_i"))
    cover_url = (
        OPENLIBRARY_COVER_URL.format(cover_id=cover_id)
        if cover_id is not None and cover_id > 0
        else ""
    )

    external_identifiers: dict[str, object] = {
        "openlibrary_work_id": work_id,
        "metadata_provider": SOURCE_OPENLIBRARY,
        "sample_seed": seed,
        "sample_offset": sample_offset,
        "first_publish_year": _year(work.get("first_publish_year")),
    }
    if edition_id:
        external_identifiers["openlibrary_edition_id"] = edition_id
    if author_ids:
        external_identifiers["openlibrary_author_ids"] = author_ids
    ebook_access = _first_text(edition.get("ebook_access"))
    if ebook_access:
        external_identifiers["ebook_access"] = ebook_access

    return ImportedPublicDomainRecord(
        source_identifier=work_id,
        title=title,
        source_url=OPENLIBRARY_WORK_URL.format(identifier=work_id),
        license_note=(
            "Open Library metadata; no new rights asserted. "
            "Selected public-access edition; jurisdictional rights may vary."
        ),
        contributors=contributors,
        description=description,
        publisher=publisher,
        publication_year=publication_year,
        language=language,
        isbn=isbn,
        cover_url=cover_url,
        subjects=subjects,
        external_identifiers=external_identifiers,
    )


def _load_openlibrary_records(
    api: _JsonApiClient,
    *,
    limit: int,
    options: _LoadOptions,
) -> list[ImportedPublicDomainRecord]:
    """Load a deterministic, source-snapshot-dependent Open Library window."""

    query = _openlibrary_search_query(options.language)
    starting_offset = (abs(options.seed) % OPENLIBRARY_SAMPLE_WINDOWS) * OPENLIBRARY_PAGE_SIZE
    offset = starting_offset
    wrapped = False
    records: list[ImportedPublicDomainRecord] = []
    seen_identifiers: set[str] = set()
    max_requests = max(5, math.ceil(limit / OPENLIBRARY_PAGE_SIZE) + 5)

    for _ in range(max_requests):
        remaining = limit - len(records)
        if remaining <= 0:
            break
        page_size = _openlibrary_page_size(remaining)
        payload = _openlibrary_page(
            api,
            query=query,
            language=options.language,
            offset=offset,
            page_size=page_size,
        )
        docs = _object_list(payload.get("docs"))
        if not docs:
            next_offset = _wrap_openlibrary_offset(offset=offset, wrapped=wrapped)
            if next_offset is not None:
                offset = next_offset
                wrapped = True
                continue
            break

        _extend_openlibrary_records(
            docs,
            records=records,
            seen_identifiers=seen_identifiers,
            limit=limit,
            language=options.language,
            seed=options.seed,
            sample_offset=starting_offset,
        )

        offset, wrapped, exhausted = _advance_openlibrary_window(
            offset=offset,
            page_size=page_size,
            docs_count=len(docs),
            wrapped=wrapped,
            starting_offset=starting_offset,
        )
        if exhausted:
            break

    return records


def _openlibrary_search_query(language: str) -> str:
    """Return the committed Open Library search query for one language."""

    language_code = OPENLIBRARY_LANGUAGE_CODES[language]
    return f"language:{language_code} AND ebook_access:public AND first_publish_year:[* TO 1928]"


def _openlibrary_page_size(remaining: int) -> int:
    """Return one bounded Open Library page size for the remaining demand."""

    return min(OPENLIBRARY_PAGE_SIZE, max(20, remaining * 2))


def _openlibrary_page(
    api: _JsonApiClient,
    *,
    query: str,
    language: str,
    offset: int,
    page_size: int,
) -> dict[str, object]:
    """Fetch one Open Library search window."""

    return api.get_object(
        OPENLIBRARY_SEARCH_URL,
        params={
            "q": query,
            "fields": OPENLIBRARY_FIELDS,
            "sort": "key",
            "lang": language,
            "offset": offset,
            "limit": page_size,
        },
    )


def _wrap_openlibrary_offset(*, offset: int, wrapped: bool) -> int | None:
    """Return the wrapped offset when an empty page should restart at zero."""

    if offset and not wrapped:
        return 0
    return None


def _advance_openlibrary_window(
    *,
    offset: int,
    page_size: int,
    docs_count: int,
    wrapped: bool,
    starting_offset: int,
) -> tuple[int, bool, bool]:
    """Advance one Open Library window and report whether iteration is exhausted."""

    next_offset = offset + page_size
    if docs_count >= page_size:
        return next_offset, wrapped, False
    if not wrapped and starting_offset:
        return 0, True, False
    return next_offset, wrapped, True


def _extend_openlibrary_records(
    docs: Sequence[dict[str, object]],
    *,
    records: list[ImportedPublicDomainRecord],
    seen_identifiers: set[str],
    limit: int,
    language: str,
    seed: int,
    sample_offset: int,
) -> None:
    """Append unique parsed Open Library records up to the requested limit."""

    for work in docs:
        record = _parse_openlibrary_record(
            work,
            language=language,
            seed=seed,
            sample_offset=sample_offset,
        )
        if record is None or record.source_identifier in seen_identifiers:
            continue
        seen_identifiers.add(record.source_identifier)
        records.append(record)
        if len(records) >= limit:
            break


def load_openlibrary_records(limit: int) -> list[ImportedPublicDomainRecord]:
    """Fetch a semi-random Open Library slice using one pooled HTTPX client."""

    options = _ACTIVE_LOAD_OPTIONS.get() or _DEFAULT_LOAD_OPTIONS
    minimum_interval = 1.0 / 3.0 if options.contact_email.strip() else 1.0
    with _http_client(options) as client:
        api = _JsonApiClient(
            client,
            source_label="Open Library",
            rate_limiter=_RateLimiter(minimum_interval),
        )
        return _load_openlibrary_records(api, limit=limit, options=options)


def _parse_gutendex_record(
    book: Mapping[str, object],
    *,
    language: str,
    seed: int,
    sample_page: int,
) -> ImportedPublicDomainRecord | None:
    """Convert one Gutendex Project Gutenberg book into the import contract."""

    identifier = _safe_int(book.get("id"))
    title = _first_text(book.get("title"), max_length=255)
    if identifier is None or identifier <= 0 or not title:
        return None
    if book.get("copyright") is not False:
        return None
    media_type = _first_text(book.get("media_type"))
    if media_type and media_type.casefold() != "text":
        return None

    contributors = _gutendex_people(book.get("authors"))
    translator_names = _gutendex_people(book.get("translators"))
    subjects = _gutendex_subjects(book)
    summaries = _text_values(
        book.get("summaries"),
        max_items=1,
        max_length=MAX_DESCRIPTION_LENGTH,
    )
    description = summaries[0][:MAX_DESCRIPTION_LENGTH] if summaries else ""
    languages = _text_values(book.get("languages"), max_items=10)
    record_language = (
        language if language in languages else (languages[0] if languages else language)
    )

    formats = _object(book.get("formats"))
    json_formats = {
        key: value for key, raw_value in formats.items() if (value := _safe_url(raw_value))
    }
    cover_url = json_formats.get("image/jpeg", "")

    external_identifiers = _gutendex_external_identifiers(
        book,
        identifier=identifier,
        seed=seed,
        sample_page=sample_page,
        translator_names=translator_names,
        json_formats=json_formats,
    )

    return ImportedPublicDomainRecord(
        source_identifier=str(identifier),
        title=title,
        source_url=GUTENBERG_EBOOK_URL.format(identifier=identifier),
        license_note=(
            "Project Gutenberg metadata via Gutendex; copyright=false means "
            "public domain in the USA. Local law may differ."
        ),
        contributors=contributors,
        description=description,
        publisher="Project Gutenberg",
        # Gutenberg metadata does not provide the original print publication date.
        publication_year=None,
        language=record_language,
        # Gutendex does not provide an ISBN; do not invent one from a modern edition.
        isbn=None,
        cover_url=cover_url,
        subjects=subjects,
        external_identifiers=external_identifiers,
    )


def _gutendex_people(value: object) -> tuple[str, ...]:
    """Return distinct display names from a Gutendex person list."""

    people = _object_list(value)
    names = [name for person in people if (name := _person_display_name(person.get("name")))]
    return tuple(dict.fromkeys(names))


def _gutendex_subjects(book: Mapping[str, object]) -> tuple[str, ...]:
    """Return distinct Gutendex subjects and bookshelves."""

    return tuple(
        _text_values(
            [
                *_text_values(book.get("subjects")),
                *_text_values(book.get("bookshelves")),
            ],
            max_items=MAX_SUBJECTS,
        )
    )


def _gutendex_external_identifiers(
    book: Mapping[str, object],
    *,
    identifier: int,
    seed: int,
    sample_page: int,
    translator_names: tuple[str, ...],
    json_formats: dict[str, str],
) -> dict[str, object]:
    """Return the committed provenance payload for one Gutendex record."""

    external_identifiers: dict[str, object] = {
        "gutenberg_ebook_id": str(identifier),
        "metadata_provider": "gutendex",
        "copyright": False,
        "sample_seed": seed,
        "sample_page": sample_page,
        "formats": json_formats,
    }
    download_count = _safe_int(book.get("download_count"))
    if download_count is not None:
        external_identifiers["download_count"] = download_count
    if translator_names:
        external_identifiers["translators"] = list(translator_names)
    bookshelves = _text_values(book.get("bookshelves"), max_items=MAX_SUBJECTS)
    if bookshelves:
        external_identifiers["bookshelves"] = bookshelves
    return external_identifiers


def _load_gutenberg_records(
    api: _JsonApiClient,
    *,
    limit: int,
    options: _LoadOptions,
) -> list[ImportedPublicDomainRecord]:
    """Load a deterministic circular window from Gutendex's Gutenberg catalog."""

    params: dict[str, str | int] = {
        "languages": options.language,
        "copyright": "false",
        "mime_type": "text/",
        "sort": "ascending",
    }
    first_page = api.get_object(GUTENDEX_BOOKS_URL, params={**params, "page": 1})
    count = _safe_int(first_page.get("count")) or 0
    if count <= 0:
        return []

    total_pages = max(1, math.ceil(count / GUTENDEX_PAGE_SIZE))
    start_page = 1 + (abs(options.seed) % total_pages)
    page = start_page
    records: list[ImportedPublicDomainRecord] = []
    seen_identifiers: set[str] = set()

    for _ in range(total_pages):
        payload = (
            first_page
            if page == 1
            else api.get_object(GUTENDEX_BOOKS_URL, params={**params, "page": page})
        )
        for book in _object_list(payload.get("results")):
            record = _parse_gutendex_record(
                book,
                language=options.language,
                seed=options.seed,
                sample_page=start_page,
            )
            if record is None or record.source_identifier in seen_identifiers:
                continue
            seen_identifiers.add(record.source_identifier)
            records.append(record)
            if len(records) >= limit:
                return records
        page = 1 if page >= total_pages else page + 1

    return records


def load_gutenberg_records(limit: int) -> list[ImportedPublicDomainRecord]:
    """Fetch Project Gutenberg metadata through Gutendex with HTTPX."""

    options = _ACTIVE_LOAD_OPTIONS.get() or _DEFAULT_LOAD_OPTIONS
    with _http_client(options) as client:
        api = _JsonApiClient(client, source_label="Gutendex")
        return _load_gutenberg_records(api, limit=limit, options=options)


def _record_primary_contributor_key(record: ImportedPublicDomainRecord) -> str:
    """Return the normalized primary contributor for a source record."""

    if not record.contributors:
        return ""
    return normalize_name(record.contributors[0])


def _record_work_key(record: ImportedPublicDomainRecord) -> tuple[str, str]:
    """Return the title/primary-author identity used to share works."""

    return normalize_name(record.title), _record_primary_contributor_key(record)


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


def _deduplicate_records(
    records: Sequence[ImportedPublicDomainRecord],
) -> list[ImportedPublicDomainRecord]:
    """Keep the first occurrence of each source identifier."""

    unique: dict[str, ImportedPublicDomainRecord] = {}
    for record in records:
        unique.setdefault(record.source_identifier, record)
    return list(unique.values())


def _build_import_state(
    *,
    source_name: str,
    records: Sequence[ImportedPublicDomainRecord],
) -> _ImportState:
    """Build bounded ORM indexes for one import transaction."""

    return _ImportState(
        external_records=_existing_external_records(source_name=source_name, records=records),
        works=_existing_works_by_identity(records),
        contributors=_existing_contributors(records),
    )


def _existing_external_records(
    *,
    source_name: str,
    records: Sequence[ImportedPublicDomainRecord],
) -> dict[str, ExternalSourceRecord]:
    """Return existing provenance rows keyed by source identifier."""

    source_identifiers = list(dict.fromkeys(record.source_identifier for record in records))
    external_records: dict[str, ExternalSourceRecord] = {}
    for chunk in _chunks(source_identifiers):
        queryset = ExternalSourceRecord.objects.select_related("work", "edition__work").filter(
            source_name=source_name,
            source_identifier__in=chunk,
        )
        external_records.update({record.source_identifier: record for record in queryset})
    return external_records


def _existing_works_by_identity(
    records: Sequence[ImportedPublicDomainRecord],
) -> dict[tuple[str, str], BibliographicWork]:
    """Return existing works keyed by normalized title and primary contributor."""

    normalized_titles = list(
        dict.fromkeys(normalize_name(record.title) for record in records if record.title)
    )
    works_by_id: dict[int, BibliographicWork] = {}
    for chunk in _chunks(normalized_titles):
        for work in BibliographicWork.objects.filter(normalized_title__in=chunk):
            works_by_id[work.pk] = work

    primary_contributor_by_work = _primary_contributor_by_work(list(works_by_id))
    works: dict[tuple[str, str], BibliographicWork] = {}
    for work_id in sorted(works_by_id):
        work = works_by_id[work_id]
        key = (
            work.normalized_title,
            primary_contributor_by_work.get(work_id, ""),
        )
        works.setdefault(key, work)
    return works


def _primary_contributor_by_work(work_ids: list[int]) -> dict[int, str]:
    """Return the first contributor key for each existing work."""

    primary_contributor_by_work: dict[int, str] = {}
    for chunk in _chunks(work_ids):
        relations = (
            WorkContributor.objects.select_related("contributor")
            .filter(work_id__in=chunk)
            .order_by("work_id", "sort_order", "id")
        )
        for relation in relations:
            relation_any = cast("Any", relation)
            work_id = cast("int", relation_any.work_id)
            primary_contributor_by_work.setdefault(
                work_id,
                relation.contributor.normalized_name,
            )
    return primary_contributor_by_work


def _existing_contributors(
    records: Sequence[ImportedPublicDomainRecord],
) -> dict[str, Contributor]:
    """Return existing contributors keyed by normalized name."""

    normalized_contributors = list(
        dict.fromkeys(
            normalize_name(name)
            for record in records
            for name in record.contributors
            if normalize_name(name)
        )
    )
    contributors: dict[str, Contributor] = {}
    for chunk in _chunks(normalized_contributors):
        queryset = Contributor.objects.filter(normalized_name__in=chunk)
        contributors.update({item.normalized_name: item for item in queryset})
    return contributors


def _reindex_work(
    state: _ImportState,
    *,
    work: BibliographicWork,
    record: ImportedPublicDomainRecord,
) -> None:
    """Replace stale request-local keys for a refreshed shared work."""

    stale_keys = [key for key, candidate in state.works.items() if candidate.pk == work.pk]
    for key in stale_keys:
        state.works.pop(key, None)
    state.works[_record_work_key(record)] = work


def _upsert_contributors(
    *,
    work: BibliographicWork,
    contributor_names: tuple[str, ...],
    refresh: bool,
    state: _ImportState,
) -> None:
    """Attach source authors to one work, replacing relations on refresh."""

    if refresh:
        WorkContributor.objects.filter(work=work).delete()

    seen_names: set[str] = set()
    sort_order = 0
    for contributor_name in contributor_names:
        normalized_name = normalize_name(contributor_name)
        if not normalized_name or normalized_name in seen_names:
            continue
        seen_names.add(normalized_name)

        contributor = state.contributors.get(normalized_name)
        created = False
        if contributor is None:
            contributor, created = Contributor.objects.get_or_create(
                normalized_name=normalized_name,
                defaults={"name": contributor_name},
            )
            state.contributors[normalized_name] = contributor
        if refresh and not created and contributor.name != contributor_name:
            contributor.name = contributor_name
            contributor.save()

        WorkContributor.objects.update_or_create(
            work=work,
            contributor=contributor,
            role=ContributorRole.AUTHOR,
            defaults={"sort_order": sort_order},
        )
        sort_order += 1


def _get_or_create_work(
    record: ImportedPublicDomainRecord,
    *,
    refresh: bool,
    state: _ImportState,
) -> BibliographicWork:
    """Return the shared work row for one imported source record."""

    work_key = _record_work_key(record)
    work = state.works.get(work_key)
    if work is None:
        work = BibliographicWork.objects.create(
            title=record.title,
            description=record.description,
        )
        state.works[work_key] = work
        return work

    if refresh and (work.title != record.title or work.description != record.description):
        work.title = record.title
        work.description = record.description
        work.save()
        _reindex_work(state, work=work, record=record)
    return work


def _apply_edition_record(
    edition: BookEdition,
    *,
    work: BibliographicWork,
    source_name: str,
    record: ImportedPublicDomainRecord,
) -> None:
    """Copy normalized source metadata onto an edition and validate it."""

    edition.work = work
    edition.publisher = record.publisher
    edition.publication_year = record.publication_year
    edition.language = record.language
    edition.isbn = record.isbn
    edition.cover_url = record.cover_url
    edition.description = record.description
    edition.external_identifiers = _external_identifiers(source_name, record)
    edition.save()


def _upsert_record(
    *,
    source_name: str,
    record: ImportedPublicDomainRecord,
    refresh: bool,
    state: _ImportState,
) -> tuple[str, bool]:
    """Create or reconcile one source record inside the import transaction."""

    existing = state.external_records.get(record.source_identifier)
    now = timezone.now()
    if existing is not None:
        if not refresh:
            return "skipped", False
        existing_any = cast("Any", existing)
        edition_id = cast("int | None", existing_any.edition_id)
        work_id = cast("int | None", existing_any.work_id)
        if edition_id is None or work_id is not None:
            raise CommandError(
                "Existing catalog-import provenance must target exactly one edition."
            )

        edition = existing.edition
        assert edition is not None
        work = edition.work
        work.title = record.title
        work.description = record.description
        work.save()
        _upsert_contributors(
            work=work,
            contributor_names=record.contributors,
            refresh=True,
            state=state,
        )
        _reindex_work(state, work=work, record=record)
        _apply_edition_record(
            edition,
            work=work,
            source_name=source_name,
            record=record,
        )
        existing.source_url = record.source_url
        existing.license_note = record.license_note
        existing.fetched_at = now
        existing.save()
        return "refreshed", False

    work = _get_or_create_work(record, refresh=refresh, state=state)
    _upsert_contributors(
        work=work,
        contributor_names=record.contributors,
        refresh=False,
        state=state,
    )
    edition = BookEdition(
        work=work,
        publisher=record.publisher,
        publication_year=record.publication_year,
        language=record.language,
        isbn=record.isbn,
        cover_url=record.cover_url,
        description=record.description,
        external_identifiers=_external_identifiers(source_name, record),
    )
    edition.save()
    provenance = ExternalSourceRecord.objects.create(
        source_name=source_name,
        source_identifier=record.source_identifier,
        source_url=record.source_url,
        license_note=record.license_note,
        edition=edition,
        imported_at=now,
        fetched_at=now,
    )
    state.external_records[record.source_identifier] = provenance
    return "created", True


def _dry_run_outcomes(
    *,
    source_name: str,
    records: Sequence[ImportedPublicDomainRecord],
    refresh: bool,
) -> Counter[str]:
    """Calculate command outcomes without constructing or mutating catalog rows."""

    identifiers = list(dict.fromkeys(record.source_identifier for record in records))
    existing_count = 0
    for chunk in _chunks(identifiers):
        existing_count += ExternalSourceRecord.objects.filter(
            source_name=source_name,
            source_identifier__in=chunk,
        ).count()

    outcomes = Counter[str]()
    outcomes["created"] = len(identifiers) - existing_count
    outcomes["refreshed" if refresh else "skipped"] = existing_count
    return outcomes


class Command(BaseCommand):
    """Import a deterministic semi-random public-domain catalog slice."""

    help = (
        "Fetch and import a semi-random public-domain catalog slice from "
        "Open Library or Project Gutenberg metadata."
    )

    def add_arguments(self, parser: Any) -> None:
        """Register source, sampling, networking, and reconciliation flags."""

        parser.add_argument(
            "--source",
            choices=(SOURCE_OPENLIBRARY, SOURCE_GUTENBERG),
            required=True,
            help="Choose Open Library or Project Gutenberg metadata via Gutendex.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=DEFAULT_LIMIT,
            help=f"Number of records to import (default {DEFAULT_LIMIT}, max {MAX_API_RECORDS}).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=DEFAULT_SAMPLE_SEED,
            help=(
                "Choose a deterministic sampling window for the current source snapshot "
                f"(default {DEFAULT_SAMPLE_SEED})."
            ),
        )
        parser.add_argument(
            "--language",
            choices=tuple(sorted(OPENLIBRARY_LANGUAGE_CODES)),
            default="en",
            help="Two-letter language code used by both source filters (default en).",
        )
        parser.add_argument(
            "--contact-email",
            default=os.environ.get(CONTACT_EMAIL_ENV, ""),
            help=(
                "Contact email included in the Open Library User-Agent. "
                f"Defaults to ${CONTACT_EMAIL_ENV}."
            ),
        )
        parser.add_argument(
            "--timeout",
            type=float,
            default=DEFAULT_TIMEOUT_SECONDS,
            help=f"Per-operation HTTP timeout in seconds (default {DEFAULT_TIMEOUT_SECONDS:g}).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and validate metadata, then report database outcomes without writes.",
        )
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Reconcile existing provenance rows instead of skipping them.",
        )

    def handle(self, *_args: str, **options: object) -> None:
        """Fetch the selected source and atomically import normalized records."""

        command_options = _validated_command_options(options)
        self._warn_about_import(command_options)
        records = self._loaded_records(command_options)

        if not records:
            raise CommandError(f"{command_options.source} returned no valid importable records.")

        if command_options.dry_run:
            self._write_dry_run_result(command_options, records)
            return

        outcomes = Counter[str]()
        with transaction.atomic():
            state = _build_import_state(source_name=command_options.source, records=records)
            for record in records:
                outcome, _ = _upsert_record(
                    source_name=command_options.source,
                    record=record,
                    refresh=command_options.refresh,
                    state=state,
                )
                outcomes[outcome] += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {outcomes['created']} record(s) from {command_options.source}; "
                f"refreshed {outcomes['refreshed']} and skipped {outcomes['skipped']} "
                f"(fetched={len(records)}, seed={command_options.seed})."
            )
        )

    def _warn_about_import(self, options: _CommandOptions) -> None:
        """Emit advisory warnings for slow or anonymous import configurations."""

        if options.source == SOURCE_OPENLIBRARY and not options.contact_email:
            self.stderr.write(
                self.style.WARNING(
                    f"No Open Library contact email configured; using its lower request rate. "
                    f"Pass --contact-email or set {CONTACT_EMAIL_ENV}."
                )
            )
        if options.limit > 250:
            self.stderr.write(
                self.style.WARNING(
                    "Large API imports are intended for occasional demo seeding; "
                    "use source data dumps for recurring bulk ingestion."
                )
            )

    def _loaded_records(self, options: _CommandOptions) -> list[ImportedPublicDomainRecord]:
        """Return unique records from the selected source under one load context."""

        loader = {
            SOURCE_OPENLIBRARY: load_openlibrary_records,
            SOURCE_GUTENBERG: load_gutenberg_records,
        }[options.source]
        load_options = _LoadOptions(
            seed=options.seed,
            language=options.language,
            timeout_seconds=options.timeout_seconds,
            contact_email=options.contact_email,
        )
        token = _ACTIVE_LOAD_OPTIONS.set(load_options)
        try:
            return _deduplicate_records(loader(options.limit))
        finally:
            _ACTIVE_LOAD_OPTIONS.reset(token)

    def _write_dry_run_result(
        self,
        options: _CommandOptions,
        records: Sequence[ImportedPublicDomainRecord],
    ) -> None:
        """Write the command outcome for a dry-run import."""

        outcomes = _dry_run_outcomes(
            source_name=options.source,
            records=records,
            refresh=options.refresh,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Dry run: fetched {len(records)} valid record(s) from {options.source}; "
                f"would create {outcomes['created']}, refresh {outcomes['refreshed']}, "
                f"and skip {outcomes['skipped']} (seed={options.seed})."
            )
        )


def _validated_command_options(options: Mapping[str, object]) -> _CommandOptions:
    """Return validated CLI options for one import run."""

    command_options = _CommandOptions(
        source=cast("str", options["source"]),
        limit=cast("int", options["limit"]),
        seed=cast("int", options["seed"]),
        language=cast("str", options["language"]),
        contact_email=cast("str", options["contact_email"]).strip(),
        timeout_seconds=cast("float", options["timeout"]),
        refresh=bool(options["refresh"]),
        dry_run=bool(options["dry_run"]),
    )
    if not 1 <= command_options.limit <= MAX_API_RECORDS:
        raise CommandError(f"--limit must be between 1 and {MAX_API_RECORDS}.")
    if command_options.timeout_seconds <= 0:
        raise CommandError("--timeout must be greater than zero.")
    return command_options
