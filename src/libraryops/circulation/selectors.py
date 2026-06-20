"""Read selectors and lookup helpers for circulation workflows."""

from __future__ import annotations

from typing import Any, cast

from django.contrib.auth.models import User

from libraryops.accounts.roles import ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER
from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy, BookCopyStatus


def checkout_copy_queryset() -> Any:
    """Return the available copies a checkout workflow may select."""

    return (
        BookCopy.objects.select_related("edition", "edition__work")
        .filter(archived_at__isnull=True, status=BookCopyStatus.AVAILABLE)
        .order_by("edition__work__title", "barcode")
    )


def checkout_borrower_queryset() -> Any:
    """Return the borrowers a checkout workflow may select."""

    return User.objects.filter(groups__name=ROLE_MEMBER).order_by("email").distinct()


def return_loan_queryset() -> Any:
    """Return the active loans a return workflow may select."""

    return (
        Loan.objects.select_related("copy__edition__work", "borrower")
        .filter(returned_at__isnull=True)
        .order_by("due_at", "-checked_out_at")
    )


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

    visible_loans_queryset = visible_loans(user, role=role)
    active_loans = visible_loans_queryset.filter(returned_at__isnull=True).order_by(
        "due_at",
        "-checked_out_at",
    )
    overdue_loans = active_loans.filter(due_at__lt=now)
    recent_returns = list(
        visible_loans_queryset.filter(returned_at__isnull=False).order_by(
            "-returned_at",
            "-checked_out_at",
        )[:5]
    )
    return {
        "visible_loan_count": visible_loans_queryset.count(),
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

    edition = cast("Any", copy.edition)
    return f"{copy.barcode} · {edition.work.title}"


def loan_label(loan: Loan) -> str:
    """Return the autocomplete label for one loan."""

    copy: BookCopy = cast("BookCopy", loan.copy)
    borrower: User = cast("User", loan.borrower)
    return f"{copy_label(copy)} · {borrower_label(borrower)}"


def loan_aliases(loan: Loan) -> tuple[str, ...]:
    """Return the searchable labels for one loan."""

    copy: BookCopy = cast("BookCopy", loan.copy)
    borrower: User = cast("User", loan.borrower)
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

    return cast(
        "BookCopy | None",
        _match_choice(value, queryset, _copy_aliases),
    )


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

    return cast(
        "User | None",
        _match_choice(value, queryset, _borrower_aliases),
    )


def resolve_loan(value: str, queryset: Any) -> Loan | None:
    """Resolve one selected loan from its copy or borrower label."""

    return cast("Loan | None", _match_choice(value, queryset, loan_aliases))
