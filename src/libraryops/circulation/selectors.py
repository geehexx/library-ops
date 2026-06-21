"""Read selectors and lookup helpers for circulation workflows."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.contrib.auth.models import User
from django.db.models import Q

from libraryops.accounts.roles import ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER
from libraryops.catalog.models import BookEdition
from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy, BookCopyStatus

RECENT_RETURN_WINDOW_DAYS = 30


def _search_term(query: str | None) -> str | None:
    """Return one normalized search term or ``None`` when empty."""

    if query is None:
        return None
    cleaned = query.strip()
    return cleaned or None


def _borrower_pk(query: str) -> int | None:
    """Return the patron primary key encoded in one library identifier."""

    for candidate in (query, query.removeprefix("PATRON-"), query.removeprefix("patron-")):
        normalized = candidate.replace(" ", "")
        if normalized.isdigit():
            return int(normalized)
    return None


def _person_search_clause(query: str, *, prefix: str = "") -> Q:
    """Return the combined text clause used for borrower-style lookup."""

    first_name_field = f"{prefix}first_name" if prefix else "first_name"
    last_name_field = f"{prefix}last_name" if prefix else "last_name"
    username_field = f"{prefix}username" if prefix else "username"
    email_field = f"{prefix}email" if prefix else "email"
    clause = (
        Q(**{f"{first_name_field}__icontains": query})
        | Q(**{f"{last_name_field}__icontains": query})
        | Q(**{f"{username_field}__icontains": query})
        | Q(**{f"{email_field}__icontains": query})
    )
    terms = [term for term in query.split() if term]
    if len(terms) >= 2:
        clause |= Q(
            **{
                f"{first_name_field}__icontains": terms[0],
                f"{last_name_field}__icontains": terms[-1],
            }
        )
    return clause


def checkout_copy_queryset(query: str | None = None) -> Any:
    """Return the available copies a checkout workflow may select."""

    queryset = (
        BookCopy.objects.select_related("edition", "edition__work")
        .filter(archived_at__isnull=True, status=BookCopyStatus.AVAILABLE)
        .order_by("edition__work__title", "barcode")
    )
    search = _search_term(query)
    if search:
        queryset = queryset.filter(
            Q(barcode__icontains=search) | Q(edition__work__title__icontains=search)
        )
    return queryset


def checkout_borrower_queryset(query: str | None = None) -> Any:
    """Return the borrowers a checkout workflow may select."""

    queryset = (
        User.objects.filter(groups__name=ROLE_MEMBER)
        .order_by(
            "last_name",
            "first_name",
            "email",
        )
        .distinct()
    )
    search = _search_term(query)
    if not search:
        return queryset
    borrower_pk = _borrower_pk(search)
    query_clause = _person_search_clause(search)
    if borrower_pk is not None:
        query_clause |= Q(pk=borrower_pk)
    return queryset.filter(query_clause)


def return_loan_queryset(query: str | None = None) -> Any:
    """Return the active loans a return workflow may select."""

    queryset = (
        Loan.objects.select_related("copy__edition__work", "borrower")
        .filter(returned_at__isnull=True)
        .order_by("due_at", "-checked_out_at")
    )
    search = _search_term(query)
    if not search:
        return queryset
    borrower_pk = _borrower_pk(search)
    query_clause = (
        Q(copy__barcode__icontains=search)
        | Q(copy__edition__work__title__icontains=search)
        | _person_search_clause(search, prefix="borrower__")
    )
    if borrower_pk is not None:
        query_clause |= Q(borrower__pk=borrower_pk) | Q(borrower__id=borrower_pk)
    return queryset.filter(query_clause)


def visible_loans(user: User, *, role: str) -> Any:
    """Return the dashboard loans visible to one user role."""

    loans = Loan.objects.select_related(
        "copy__edition__work",
        "borrower",
        "copy",
        "copy__edition",
    ).order_by("-checked_out_at")
    if role == ROLE_MEMBER:
        return loans.filter(borrower=user)
    return loans


def loan_dashboard_context(user: User, *, role: str, now: Any) -> dict[str, Any]:
    """Return the dashboard slices and counts for one user role."""

    dashboard_queryset = visible_loans(user, role=role)
    active_loans = dashboard_queryset.filter(returned_at__isnull=True).order_by(
        "due_at",
        "-checked_out_at",
    )
    overdue_loans = active_loans.filter(due_at__lt=now)
    recent_return_window_start = now - timedelta(days=RECENT_RETURN_WINDOW_DAYS)
    recent_returns = list(
        dashboard_queryset.filter(
            returned_at__isnull=False,
            returned_at__gte=recent_return_window_start,
        ).order_by(
            "-returned_at",
            "-checked_out_at",
        )[:5]
    )
    visible_loan_count = active_loans.count() + len(recent_returns)
    return {
        "visible_loan_count": visible_loan_count,
        "active_loans": active_loans,
        "active_loan_count": active_loans.count(),
        "overdue_loans": overdue_loans,
        "overdue_loan_count": overdue_loans.count(),
        "recent_returns": recent_returns,
        "recent_return_count": len(recent_returns),
        "show_borrower_column": role in (ROLE_ADMIN, ROLE_LIBRARIAN),
    }


def _normalized_choice(value: str) -> str:
    """Normalize one typed choice for comparison."""

    return " ".join(value.strip().split()).casefold()


def borrower_display_name(user: Any) -> str:
    """Return a human-facing borrower name from durable user data."""

    full_name = user.get_full_name().strip()
    if full_name:
        return full_name
    username = user.get_username().strip()
    local_part = username.split("@", 1)[0]
    local_part = local_part.replace(".", " ").replace("_", " ").replace("-", " ")
    fallback = " ".join(local_part.split()).title()
    return fallback or f"Borrower {user.pk or ''}".strip()


def borrower_identifier(user: Any) -> str:
    """Return the library-style borrower identifier."""

    if user.pk is None:
        return "PATRON-UNSAVED"
    return f"PATRON-{user.pk:04d}"


def borrower_label(user: Any) -> str:
    """Return the autocomplete label for one borrower."""

    return f"{borrower_display_name(user)} ({borrower_identifier(user)})"


def copy_label(copy: BookCopy) -> str:
    """Return the autocomplete label for one copy."""

    edition = copy.edition
    if not isinstance(edition, BookEdition):
        raise TypeError("Expected copy.edition to be a BookEdition.")
    return f"{copy.barcode} · {edition.work.title}"


def loan_label(loan: Loan) -> str:
    """Return the autocomplete label for one loan."""

    copy = loan.copy
    if not isinstance(copy, BookCopy):
        raise TypeError("Expected loan.copy to be a BookCopy.")
    borrower = loan.borrower
    if not isinstance(borrower, User):
        raise TypeError("Expected loan.borrower to be a User.")
    return f"{copy_label(copy)} · {borrower_label(borrower)}"


def loan_aliases(loan: Loan) -> tuple[str, ...]:
    """Return the searchable labels for one loan."""

    copy = loan.copy
    if not isinstance(copy, BookCopy):
        raise TypeError("Expected loan.copy to be a BookCopy.")
    borrower = loan.borrower
    if not isinstance(borrower, User):
        raise TypeError("Expected loan.borrower to be a User.")
    return (
        loan_label(loan),
        copy_label(copy),
        copy.barcode,
        borrower_label(borrower),
        borrower_display_name(borrower),
        borrower_identifier(borrower),
        str(loan.pk) if loan.pk is not None else "",
    )


def _match_choice(
    value: str,
    queryset: Any,
    aliases: Any,
) -> Any | None:
    """Return the unique queryset instance matching one typed value."""

    normalized_value = _normalized_choice(value)
    if not normalized_value:
        return None
    candidates = list(queryset)
    exact_matches = [
        instance
        for instance in candidates
        if normalized_value in {_normalized_choice(alias) for alias in aliases(instance)}
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if exact_matches:
        return None
    partial_matches = [
        instance
        for instance in candidates
        if any(normalized_value in _normalized_choice(alias) for alias in aliases(instance))
    ]
    return partial_matches[0] if len(partial_matches) == 1 else None


def resolve_copy(value: str, queryset: Any) -> BookCopy | None:
    """Resolve one selected copy from its display label or barcode."""

    def _copy_aliases(copy: Any) -> tuple[str, str, str, str]:
        return (
            copy_label(copy),
            copy.barcode,
            copy.edition.work.title,
            str(copy.pk) if copy.pk is not None else "",
        )

    resolved = _match_choice(value, queryset, _copy_aliases)
    return resolved if isinstance(resolved, BookCopy) else None


def resolve_borrower(value: str, queryset: Any) -> User | None:
    """Resolve one selected borrower from a human name or patron code."""

    def _borrower_aliases(user: Any) -> tuple[str, str, str, str, str]:
        return (
            borrower_label(user),
            borrower_display_name(user),
            borrower_identifier(user),
            user.email,
            user.username,
        )

    resolved = _match_choice(value, queryset, _borrower_aliases)
    return resolved if isinstance(resolved, User) else None


def resolve_loan(value: str, queryset: Any) -> Loan | None:
    """Resolve one selected loan from its copy or borrower label."""

    resolved = _match_choice(value, queryset, loan_aliases)
    return resolved if isinstance(resolved, Loan) else None
