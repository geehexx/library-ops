"""Factory layer for Django model and auth test setup."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Protocol

import factory
from django.contrib.auth.models import Group, User
from django.utils import timezone

from libraryops.accounts.roles import ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER
from libraryops.catalog.models import (
    BibliographicWork,
    BookEdition,
    Contributor,
    ContributorRole,
    WorkContributor,
)
from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy

Sequence: Any = factory.Sequence  # pyright: ignore[reportPrivateImportUsage]
LazyAttribute: Any = factory.LazyAttribute  # pyright: ignore[reportPrivateImportUsage]
LazyFunction: Any = factory.LazyFunction  # pyright: ignore[reportPrivateImportUsage]
PostGenerationMethodCall: Any = factory.PostGenerationMethodCall  # pyright: ignore[reportPrivateImportUsage]
SubFactory: Any = factory.SubFactory  # pyright: ignore[reportPrivateImportUsage]
post_generation: Any = factory.post_generation  # pyright: ignore[reportPrivateImportUsage, reportUnknownVariableType, reportUnknownMemberType]


class _UserResolver(Protocol):
    """Protocol for the minimal user shape needed by factory helpers."""

    username: str


def _group_name_sequence(n: int) -> str:
    """Return a deterministic group name for factory sequences."""

    return f"Group {n}"


def _user_username_sequence(n: int) -> str:
    """Return a deterministic demo username for factory sequences."""

    return f"user{n}@libraryops.test"


def _user_email(user: _UserResolver) -> str:
    """Mirror the factory username onto the stored email address."""

    return str(user.username)


def _work_title_sequence(n: int) -> str:
    """Return a deterministic bibliographic title for factory sequences."""

    return f"Example Title {n}"


def _contributor_name_sequence(n: int) -> str:
    """Return a deterministic contributor name for factory sequences."""

    return f"Contributor {n}"


def _book_copy_barcode_sequence(n: int) -> str:
    """Return a deterministic barcode for factory sequences."""

    return f"BC-{n:04d}"


def _loan_due_at() -> datetime:
    """Return the standard loan due date used by factories."""

    return timezone.now() + timedelta(days=14)


def build_isbn13(seed: int) -> str:
    """Return a deterministic valid ISBN-13 for a numeric seed."""

    base = f"978000000{seed:03d}"
    check_total = sum((1 if index % 2 == 0 else 3) * int(digit) for index, digit in enumerate(base))
    check_digit = (10 - (check_total % 10)) % 10
    return f"{base}{check_digit}"


class GroupFactory(factory.django.DjangoModelFactory[Group]):
    """Create one Django auth group."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Bind the factory to Django's Group model."""

        model = Group

    name: Any = Sequence(_group_name_sequence)


class UserFactory(factory.django.DjangoModelFactory[User]):
    """Create one Django auth user."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Bind the factory to Django's User model."""

        model = User

    username: Any = Sequence(_user_username_sequence)
    email: Any = LazyAttribute(_user_email)
    password: Any = PostGenerationMethodCall("set_password", "library-ops-test")
    is_staff = False
    is_superuser = False

    @post_generation
    def groups(self, create: bool, extracted: list[Group] | None, **_kwargs: object) -> None:
        """Attach any provided groups after the user is created."""

        if create and extracted:
            self.groups.add(*extracted)


class AdminUserFactory(UserFactory):
    """Create an admin user tied to the seeded Admin group."""

    is_staff = True
    is_superuser = True

    @post_generation
    def groups(self, create: bool, extracted: list[Group] | None, **_kwargs: object) -> None:
        """Attach the seeded Admin group unless explicit groups were provided."""

        if not create:
            return
        groups = extracted or [Group.objects.get_or_create(name=ROLE_ADMIN)[0]]
        self.groups.add(*groups)


class LibrarianUserFactory(UserFactory):
    """Create a librarian user tied to the seeded Librarian group."""

    is_staff = True

    @post_generation
    def groups(self, create: bool, extracted: list[Group] | None, **_kwargs: object) -> None:
        """Attach the seeded Librarian group unless explicit groups were provided."""

        if not create:
            return
        groups = extracted or [Group.objects.get_or_create(name=ROLE_LIBRARIAN)[0]]
        self.groups.add(*groups)


class MemberUserFactory(UserFactory):
    """Create a member user tied to the seeded Member group."""

    @post_generation
    def groups(self, create: bool, extracted: list[Group] | None, **_kwargs: object) -> None:
        """Attach the seeded Member group unless explicit groups were provided."""

        if not create:
            return
        groups = extracted or [Group.objects.get_or_create(name=ROLE_MEMBER)[0]]
        self.groups.add(*groups)


class BibliographicWorkFactory(factory.django.DjangoModelFactory[BibliographicWork]):
    """Create one bibliographic work."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Bind the factory to the catalog work model."""

        model = BibliographicWork

    title: Any = Sequence(_work_title_sequence)


class ContributorFactory(factory.django.DjangoModelFactory[Contributor]):
    """Create one contributor."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Bind the factory to the contributor model."""

        model = Contributor

    name: Any = Sequence(_contributor_name_sequence)


class WorkContributorFactory(factory.django.DjangoModelFactory[WorkContributor]):
    """Create one contributor relationship for a work."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Bind the factory to the work-contributor model."""

        model = WorkContributor

    work: Any = SubFactory(BibliographicWorkFactory)
    contributor: Any = SubFactory(ContributorFactory)
    role = ContributorRole.AUTHOR
    sort_order = 0


class BookEditionFactory(factory.django.DjangoModelFactory[BookEdition]):
    """Create one edition for a bibliographic work."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Bind the factory to the edition model."""

        model = BookEdition

    work: Any = SubFactory(BibliographicWorkFactory)
    publisher = "Example Press"
    publication_year = 2024
    language = "en"
    isbn: Any = Sequence(build_isbn13)


class BookCopyFactory(factory.django.DjangoModelFactory[BookCopy]):
    """Create one borrowable copy."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Bind the factory to the book-copy model."""

        model = BookCopy

    edition: Any = SubFactory(BookEditionFactory)
    barcode: Any = Sequence(_book_copy_barcode_sequence)
    shelf_location = "A1"


class LoanFactory(factory.django.DjangoModelFactory[Loan]):
    """Create one loan row."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Bind the factory to the loan model."""

        model = Loan

    copy: Any = SubFactory(BookCopyFactory)
    borrower: Any = SubFactory(MemberUserFactory)
    checked_out_at: Any = LazyFunction(timezone.now)
    due_at: Any = LazyFunction(_loan_due_at)
    returned_at = None
