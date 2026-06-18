"""Catalog API routers for Django Ninja."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any, Literal, cast

from django.contrib.auth.models import User  # noqa: TC002
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest  # noqa: TC002
from ninja import Field, Router, Schema, Status
from pydantic import model_validator

from libraryops.catalog import selectors
from libraryops.catalog.models import BibliographicWork, BookEdition
from libraryops.inventory.models import BookCopy, BookCopyStatus

MutableCopyStatus = Literal["available", "on_loan", "maintenance", "lost"]


class CopyResponse(Schema):
    """Serialized copy representation."""

    id: int
    edition_id: int
    barcode: str
    status: BookCopyStatus
    shelf_location: str
    condition_note: str
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CopyCreateIn(Schema):
    """Payload for creating a copy."""

    edition: int = Field(ge=1)
    barcode: str = Field(min_length=1, max_length=64)
    status: MutableCopyStatus = "available"
    shelf_location: str = ""
    condition_note: str = ""


class CopyUpdateIn(Schema):
    """Payload for updating a copy."""

    edition: int | None = Field(default=None, ge=1)
    barcode: str | None = Field(default=None, min_length=1, max_length=64)
    status: MutableCopyStatus | None = None
    shelf_location: str | None = None
    condition_note: str | None = None

    @model_validator(mode="after")
    def _require_change(self) -> CopyUpdateIn:
        if (
            self.edition is None
            and self.barcode is None
            and self.status is None
            and self.shelf_location is None
            and self.condition_note is None
        ):
            raise ValueError("At least one copy field must be provided.")
        return self


class EditionResponse(Schema):
    """Serialized edition representation."""

    id: int
    work_id: int
    publisher: str
    publication_year: int | None
    language: str
    isbn: str | None
    description: str
    external_identifiers: dict[str, Any]
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    copies: list[CopyResponse] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]


class EditionCreateIn(Schema):
    """Payload for creating an edition."""

    work: int = Field(ge=1)
    publisher: str = ""
    publication_year: int | None = None
    language: str = Field(default="en", min_length=1, max_length=16)
    isbn: str | None = Field(default=None, min_length=1)
    description: str = ""
    external_identifiers: dict[str, Any] = Field(default_factory=dict)


class EditionUpdateIn(Schema):
    """Payload for updating an edition."""

    work: int | None = Field(default=None, ge=1)
    publisher: str | None = None
    publication_year: int | None = None
    language: str | None = Field(default=None, min_length=1, max_length=16)
    isbn: str | None = Field(default=None, min_length=1)
    description: str | None = None
    external_identifiers: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _require_change(self) -> EditionUpdateIn:
        if (
            self.work is None
            and self.publisher is None
            and self.publication_year is None
            and self.language is None
            and self.isbn is None
            and self.description is None
            and self.external_identifiers is None
        ):
            raise ValueError("At least one edition field must be provided.")
        return self


class WorkResponse(Schema):
    """Serialized work representation."""

    id: int
    title: str
    description: str
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    editions: list[EditionResponse] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]


class WorkCreateIn(Schema):
    """Payload for creating a work."""

    title: str = Field(min_length=1, max_length=255)
    description: str = ""


class WorkUpdateIn(Schema):
    """Payload for updating a work."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

    @model_validator(mode="after")
    def _require_change(self) -> WorkUpdateIn:
        if self.title is None and self.description is None:
            raise ValueError("At least one work field must be provided.")
        return self


works_router = Router(tags=["catalog", "works"])
editions_router = Router(tags=["catalog", "editions"])
copies_router = Router(tags=["catalog", "copies"])


def _mutation_actor(request: HttpRequest) -> User:
    """Return the authenticated request user for a catalog mutation."""

    user = request.user
    if not user.is_authenticated:
        raise PermissionDenied("Catalog mutations require a logged-in librarian or admin.")
    return cast("User", user)


def _work_response(work: BibliographicWork) -> WorkResponse:
    """Serialize a work response."""

    editions = cast("Any", work).editions.all()
    return WorkResponse(
        id=int(work.pk or 0),
        title=work.title,
        description=work.description,
        archived_at=work.archived_at,
        created_at=work.created_at,
        updated_at=work.updated_at,
        editions=[_edition_response(edition) for edition in editions],
    )


def _edition_response(edition: BookEdition) -> EditionResponse:
    """Serialize an edition response."""

    copies = cast("Any", edition).copies.all()
    return EditionResponse(
        id=int(edition.pk or 0),
        work_id=int(cast("Any", edition.work).pk or 0),
        publisher=edition.publisher,
        publication_year=edition.publication_year,
        language=edition.language,
        isbn=edition.isbn,
        description=edition.description,
        external_identifiers=edition.external_identifiers,
        archived_at=edition.archived_at,
        created_at=edition.created_at,
        updated_at=edition.updated_at,
        copies=[_copy_response(copy) for copy in copies],
    )


def _copy_response(copy: BookCopy) -> CopyResponse:
    """Serialize a copy response."""

    return CopyResponse(
        id=int(copy.pk or 0),
        edition_id=int(cast("Any", copy.edition).pk or 0),
        barcode=copy.barcode,
        status=BookCopyStatus(copy.status),
        shelf_location=copy.shelf_location,
        condition_note=copy.condition_note,
        archived_at=copy.archived_at,
        created_at=copy.created_at,
        updated_at=copy.updated_at,
    )


@works_router.get("", response=list[WorkResponse])
def list_works(request: HttpRequest) -> list[WorkResponse]:  # noqa: ARG001
    """Return the active catalog works."""

    return [_work_response(work) for work in selectors.work_list()]


@works_router.get("/{work_id}", response=WorkResponse)
def get_work(request: HttpRequest, work_id: int) -> WorkResponse:  # noqa: ARG001
    """Return one active work."""

    return _work_response(selectors.work_detail(work_id))


@works_router.post("", response={201: WorkResponse})
def create_work(request: HttpRequest, payload: WorkCreateIn) -> Status[WorkResponse]:
    """Create one work."""

    work = BibliographicWork.objects.create_work(
        actor=_mutation_actor(request),
        title=payload.title,
        description=payload.description,
    )
    return Status(201, _work_response(work))


@works_router.put("/{work_id}", response=WorkResponse)
def update_work(request: HttpRequest, work_id: int, payload: WorkUpdateIn) -> WorkResponse:
    """Update one work."""

    work = selectors.work_detail(work_id)
    updated = BibliographicWork.objects.update_work(
        actor=_mutation_actor(request),
        work=work,
        title=payload.title,
        description=payload.description,
    )
    return _work_response(updated)


@works_router.delete("/{work_id}", response=WorkResponse)
def archive_work(request: HttpRequest, work_id: int) -> WorkResponse:
    """Archive one work."""

    work = selectors.work_detail(work_id)
    archived = BibliographicWork.objects.archive_work(actor=_mutation_actor(request), work=work)
    return _work_response(archived)


@editions_router.get("", response=list[EditionResponse])
def list_editions(request: HttpRequest) -> list[EditionResponse]:  # noqa: ARG001
    """Return the active catalog editions."""

    return [_edition_response(edition) for edition in selectors.edition_list()]


@editions_router.get("/{edition_id}", response=EditionResponse)
def get_edition(request: HttpRequest, edition_id: int) -> EditionResponse:  # noqa: ARG001
    """Return one active edition."""

    return _edition_response(selectors.edition_detail(edition_id))


@editions_router.post("", response={201: EditionResponse})
def create_edition(
    request: HttpRequest,
    payload: EditionCreateIn,
) -> Status[EditionResponse]:
    """Create one edition."""

    edition = BookEdition.objects.create_edition(
        actor=_mutation_actor(request),
        work=selectors.work_detail(payload.work),
        publisher=payload.publisher,
        publication_year=payload.publication_year,
        language=payload.language,
        isbn=payload.isbn,
        description=payload.description,
        external_identifiers=payload.external_identifiers,
    )
    return Status(201, _edition_response(edition))


@editions_router.put("/{edition_id}", response=EditionResponse)
def update_edition(
    request: HttpRequest,
    edition_id: int,
    payload: EditionUpdateIn,
) -> EditionResponse:
    """Update one edition."""

    edition = selectors.edition_detail(edition_id)
    updated = BookEdition.objects.update_edition(
        actor=_mutation_actor(request),
        edition=edition,
        work=selectors.work_detail(payload.work) if payload.work is not None else None,
        publisher=payload.publisher,
        publication_year=payload.publication_year,
        language=payload.language,
        isbn=payload.isbn,
        description=payload.description,
        external_identifiers=payload.external_identifiers,
    )
    return _edition_response(updated)


@editions_router.delete("/{edition_id}", response=EditionResponse)
def archive_edition(request: HttpRequest, edition_id: int) -> EditionResponse:
    """Archive one edition."""

    edition = selectors.edition_detail(edition_id)
    archived = BookEdition.objects.archive_edition(actor=_mutation_actor(request), edition=edition)
    return _edition_response(archived)


@copies_router.get("", response=list[CopyResponse])
def list_copies(request: HttpRequest) -> list[CopyResponse]:  # noqa: ARG001
    """Return the active copies."""

    return [_copy_response(copy) for copy in selectors.copy_list()]


@copies_router.get("/{copy_id}", response=CopyResponse)
def get_copy(request: HttpRequest, copy_id: int) -> CopyResponse:  # noqa: ARG001
    """Return one active copy."""

    return _copy_response(selectors.copy_detail(copy_id))


@copies_router.post("", response={201: CopyResponse})
def create_copy(
    request: HttpRequest,
    payload: CopyCreateIn,
) -> Status[CopyResponse]:
    """Create one copy."""

    copy = BookCopy.objects.create_copy(
        actor=_mutation_actor(request),
        edition=selectors.edition_detail(payload.edition),
        barcode=payload.barcode,
        status=payload.status,
        shelf_location=payload.shelf_location,
        condition_note=payload.condition_note,
    )
    return Status(201, _copy_response(copy))


@copies_router.put("/{copy_id}", response=CopyResponse)
def update_copy(
    request: HttpRequest,
    copy_id: int,
    payload: CopyUpdateIn,
) -> CopyResponse:
    """Update one copy."""

    copy = selectors.copy_detail(copy_id)
    updated = BookCopy.objects.update_copy(
        actor=_mutation_actor(request),
        copy=copy,
        edition=selectors.edition_detail(payload.edition) if payload.edition is not None else None,
        barcode=payload.barcode,
        status=payload.status,
        shelf_location=payload.shelf_location,
        condition_note=payload.condition_note,
    )
    return _copy_response(updated)


@copies_router.delete("/{copy_id}", response=CopyResponse)
def archive_copy(request: HttpRequest, copy_id: int) -> CopyResponse:
    """Archive one copy."""

    copy = selectors.copy_detail(copy_id)
    archived = BookCopy.objects.archive_copy(actor=_mutation_actor(request), copy=copy)
    return _copy_response(archived)
