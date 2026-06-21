"""Seed reproducible circulation examples for the demo dataset."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import random
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_date, parse_datetime
from django.utils import timezone

from libraryops.accounts.roles import ROLE_MEMBER
from libraryops.catalog.models import BookEdition
from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy, BookCopyStatus

EXAMPLE_MEMBER_EMAIL = "member@libraryops.demo"
EXAMPLE_ACTOR_EMAILS = ("librarian@libraryops.demo", "admin@libraryops.demo")
HISTORY_COPY_PREFIX = "CIRC-HIST-"
HISTORY_RANDOM_SEED = 20260622
HISTORY_YEARS = 5
HISTORY_RETURN_BUFFER_DAYS = 45


@dataclass(frozen=True, slots=True)
class ExampleLoanPlan:
    """Describe one fixed circulation example."""

    barcode: str
    edition_index: int
    checked_out_days_ago: int
    due_in_days: int
    returned_days_ago: int | None = None

    @property
    def is_returned(self) -> bool:
        """Return whether this example should end in a returned state."""

        return self.returned_days_ago is not None


EXAMPLE_LOAN_PLANS: tuple[ExampleLoanPlan, ...] = (
    ExampleLoanPlan(
        barcode="CIRC-DEMO-001",
        edition_index=0,
        checked_out_days_ago=2,
        due_in_days=12,
    ),
    ExampleLoanPlan(
        barcode="CIRC-DEMO-002",
        edition_index=1,
        checked_out_days_ago=21,
        due_in_days=-7,
    ),
    ExampleLoanPlan(
        barcode="CIRC-DEMO-003",
        edition_index=0,
        checked_out_days_ago=14,
        due_in_days=-4,
        returned_days_ago=2,
    ),
)


def _load_user(user_model: Any, email: str) -> Any:
    """Return one seeded user or fail fast with a clear message."""

    user = user_model.objects.filter(email=email).first()
    if user is None:
        raise CommandError(
            "Missing seeded demo users. Run `python manage.py seed_roles` and "
            "`python manage.py seed_demo_users` before seeding circulation examples."
        )
    return user


def _load_actor(user_model: Any) -> Any:
    """Return a privileged seeded actor for inventory and circulation mutations."""

    for email in EXAMPLE_ACTOR_EMAILS:
        user = user_model.objects.filter(email=email).first()
        if user is not None:
            return user
    raise CommandError(
        "Missing seeded demo staff users. Run `python manage.py seed_demo_users` before "
        "seeding circulation examples."
    )


def _load_editions() -> list[BookEdition]:
    """Return the seeded catalog editions used for circulation examples."""

    editions = list(
        BookEdition.objects.select_related("work").order_by("work__title", "isbn", "pk")
    )
    if not editions:
        raise CommandError(
            "Missing seeded catalog records. Run `python manage.py import_public_domain_catalog` "
            "before seeding circulation examples."
        )
    return editions


def _clear_example_snapshot() -> None:
    """Remove the dedicated demo circulation rows before rebuilding them."""

    example_copies = BookCopy.objects.filter(barcode__in={plan.barcode for plan in EXAMPLE_LOAN_PLANS})
    history_copies = BookCopy.objects.filter(barcode__startswith=HISTORY_COPY_PREFIX)
    Loan.objects.filter(copy__in=example_copies).delete()
    example_copies.delete()
    Loan.objects.filter(copy__in=history_copies).delete()
    history_copies.delete()


def _ensure_copy(*, actor: Any, edition: BookEdition, barcode: str) -> BookCopy:
    """Return the dedicated example copy, recreating it if it drifted."""

    copy = BookCopy.objects.select_related("edition").filter(barcode=barcode).first()
    if copy is None:
        return BookCopy.objects.create_copy(actor=actor, edition=edition, barcode=barcode)
    copy_edition_id = getattr(copy, "edition_id", None)
    if copy_edition_id != edition.pk or copy.archived_at is not None:
        Loan.objects.filter(copy=copy).delete()
        copy.delete()
        return BookCopy.objects.create_copy(actor=actor, edition=edition, barcode=barcode)
    return copy


def _expected_timestamps(
    plan: ExampleLoanPlan,
    anchor: datetime,
) -> tuple[datetime, datetime, datetime | None]:
    """Return the timestamp trio for one circulation example."""

    checked_out_at = anchor - timedelta(days=plan.checked_out_days_ago)
    due_at = anchor + timedelta(days=plan.due_in_days)
    returned_at = None
    if plan.returned_days_ago is not None:
        returned_at = anchor - timedelta(days=plan.returned_days_ago)
    return checked_out_at, due_at, returned_at


def _parse_anchor(value: str | None) -> datetime:
    """Return one timezone-aware anchor timestamp."""

    if value is None:
        return timezone.now().replace(microsecond=0)
    parsed_datetime = parse_datetime(value)
    if parsed_datetime is not None:
        if timezone.is_naive(parsed_datetime):
            parsed_datetime = timezone.make_aware(parsed_datetime, timezone.get_current_timezone())
        return parsed_datetime.replace(microsecond=0)
    parsed_date = parse_date(value)
    if parsed_date is not None:
        return timezone.make_aware(
            datetime.combine(parsed_date, datetime.min.time()),
            timezone.get_current_timezone(),
        ).replace(microsecond=0)
    raise CommandError("--as-of must be an ISO date or datetime.")


def _load_member_borrowers(user_model: Any) -> list[Any]:
    """Return the deterministic member borrower pool."""

    borrowers = list(
        user_model.objects.filter(groups__name=ROLE_MEMBER).order_by("email").distinct()
    )
    if not borrowers:
        raise CommandError(
            "Missing seeded member borrowers. Run `python manage.py seed_demo_users` before "
            "seeding circulation examples."
        )
    return borrowers


def _history_loan_target(rank: int, *, random_value: float) -> int:
    """Return the deterministic historical loan target for one edition rank."""

    if rank > 1 and random_value < 0.1:
        return 0
    return max(1, round(8 / (rank**0.8)))


def _copy_target_for_history(loan_target: int) -> int:
    """Return the number of background copies needed for one edition history."""

    return min(4, max(1, 1 + loan_target // 4))


def _ensure_history_copy(
    *,
    actor: Any,
    edition: BookEdition,
    barcode: str,
    shelf_location: str,
) -> BookCopy:
    """Return one deterministic background-history copy."""

    copy = BookCopy.objects.select_related("edition").filter(barcode=barcode).first()
    if copy is None:
        return BookCopy.objects.create_copy(
            actor=actor,
            edition=edition,
            barcode=barcode,
            shelf_location=shelf_location,
        )
    if getattr(copy, "edition_id", None) != edition.pk or copy.archived_at is not None:
        Loan.objects.filter(copy=copy).delete()
        copy.delete()
        return BookCopy.objects.create_copy(
            actor=actor,
            edition=edition,
            barcode=barcode,
            shelf_location=shelf_location,
        )
    if copy.status != BookCopyStatus.AVAILABLE.value or copy.shelf_location != shelf_location:
        copy.status = BookCopyStatus.AVAILABLE.value
        copy.shelf_location = shelf_location
        copy.save(update_fields=["status", "shelf_location", "updated_at"])
    return copy


def _seed_background_history(
    *,
    actor: Any,
    editions: list[BookEdition],
    borrowers: list[Any],
    anchor: datetime,
) -> tuple[int, int]:
    """Create deterministic older returned history without polluting the dashboard."""

    if BookCopy.objects.filter(barcode__startswith=HISTORY_COPY_PREFIX).exists():
        return 0, 0

    rng = random.Random(HISTORY_RANDOM_SEED)
    history_loan_count = 0
    history_copy_count = 0
    history_span_days = max(HISTORY_RETURN_BUFFER_DAYS + 30, HISTORY_YEARS * 365)

    for rank, edition in enumerate(editions, start=1):
        loan_target = _history_loan_target(rank, random_value=rng.random())
        if loan_target <= 0:
            continue
        copy_count = _copy_target_for_history(loan_target)
        copies = [
            _ensure_history_copy(
                actor=actor,
                edition=edition,
                barcode=f"{HISTORY_COPY_PREFIX}{edition.pk:04d}-{copy_index:02d}",
                shelf_location=f"Demo-{rank:02d}",
            )
            for copy_index in range(1, copy_count + 1)
        ]
        history_copy_count += len(copies)
        for loan_index in range(loan_target):
            copy = copies[loan_index % len(copies)]
            borrower = borrowers[(loan_index + rank) % len(borrowers)]
            return_age_days = HISTORY_RETURN_BUFFER_DAYS + rng.randint(
                0,
                history_span_days - HISTORY_RETURN_BUFFER_DAYS,
            )
            returned_at = anchor - timedelta(
                days=return_age_days,
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
            )
            checkout_length_days = 7 + rng.randint(0, 21)
            checked_out_at = returned_at - timedelta(
                days=checkout_length_days,
                hours=rng.randint(0, 12),
            )
            due_at = checked_out_at + timedelta(days=14 + rng.randint(-2, 7))
            Loan.objects.create(
                copy=copy,
                borrower=borrower,
                checked_out_at=checked_out_at,
                due_at=due_at,
                returned_at=returned_at,
            )
            history_loan_count += 1
        if any(copy.status != BookCopyStatus.AVAILABLE.value for copy in copies):
            BookCopy.objects.filter(pk__in=[copy.pk for copy in copies]).update(
                status=BookCopyStatus.AVAILABLE.value
            )
    return history_copy_count, history_loan_count


def _select_existing_loan(copy: BookCopy, *, returned: bool) -> Loan | None:
    """Pick one existing example loan for the target state, if present."""

    loans = Loan.objects.filter(copy=copy)
    if returned:
        loan = loans.filter(returned_at__isnull=False).order_by("-returned_at", "-pk").first()
        return loan or loans.order_by("-checked_out_at", "-pk").first()
    loan = loans.filter(returned_at__isnull=True).order_by("-checked_out_at", "-pk").first()
    return loan or loans.order_by("-checked_out_at", "-pk").first()


def _prune_duplicate_loans(copy: BookCopy, keep: Loan | None) -> None:
    """Delete any extra loan rows for a dedicated demo copy."""

    query = Loan.objects.filter(copy=copy)
    if keep is not None:
        query = query.exclude(pk=keep.pk)
    query.delete()


def _sync_active_loan(
    *,
    actor: Any,
    borrower: Any,
    copy: BookCopy,
    plan: ExampleLoanPlan,
    anchor: datetime,
) -> Loan:
    """Create or reconcile one active or overdue loan example."""

    checked_out_at, due_at, _ = _expected_timestamps(plan, anchor)
    loan = _select_existing_loan(copy, returned=False)
    if loan is None:
        loan = Loan.objects.create(
            copy=copy,
            borrower=borrower,
            checked_out_at=checked_out_at,
            due_at=due_at,
        )
        copy.status = BookCopyStatus.ON_LOAN.value
        copy.save(update_fields=["status", "updated_at"])
    else:
        loan.borrower = borrower
        loan.checked_out_at = checked_out_at
        loan.due_at = due_at
        loan.returned_at = None
        loan.save(update_fields=["borrower", "checked_out_at", "due_at", "returned_at"])
    _prune_duplicate_loans(copy, loan)
    if copy.status != BookCopyStatus.ON_LOAN.value:
        copy.status = BookCopyStatus.ON_LOAN.value
        copy.save(update_fields=["status", "updated_at"])
    return loan


def _sync_returned_loan(
    *,
    actor: Any,
    borrower: Any,
    copy: BookCopy,
    plan: ExampleLoanPlan,
    anchor: datetime,
) -> Loan:
    """Create or reconcile one returned loan example."""

    checked_out_at, due_at, returned_at = _expected_timestamps(plan, anchor)
    if returned_at is None:
        raise CommandError("Returned circulation examples require a returned timestamp.")

    loan = _select_existing_loan(copy, returned=True)
    if loan is None:
        loan = Loan.objects.create(
            copy=copy,
            borrower=borrower,
            checked_out_at=checked_out_at,
            due_at=due_at,
            returned_at=returned_at,
        )
    else:
        loan.borrower = borrower
        loan.checked_out_at = checked_out_at
        loan.due_at = due_at
        loan.returned_at = returned_at
        loan.save(update_fields=["borrower", "checked_out_at", "due_at", "returned_at"])
    _prune_duplicate_loans(copy, loan)
    if copy.status != BookCopyStatus.AVAILABLE.value:
        copy.status = BookCopyStatus.AVAILABLE.value
        copy.save(update_fields=["status", "updated_at"])
    return loan


class Command(BaseCommand):
    """Seed the disposable demo circulation snapshot."""

    help = "Create reproducible active, overdue, and returned loan examples."

    def add_arguments(self, parser: Any) -> None:
        """Register command flags."""

        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Delete the dedicated demo copies and loans before rebuilding the snapshot.",
        )
        parser.add_argument(
            "--as-of",
            type=str,
            default=None,
            help="ISO date or datetime anchor for deterministic circulation history.",
        )

    @transaction.atomic
    def handle(self, *_args: str, **options: object) -> None:
        """Create or refresh the circulation seed snapshot."""

        user_model = get_user_model()
        member = _load_user(user_model, EXAMPLE_MEMBER_EMAIL)
        actor = _load_actor(user_model)
        borrowers = _load_member_borrowers(user_model)

        if bool(options["refresh"]):
            _clear_example_snapshot()

        editions = _load_editions()
        anchor = _parse_anchor(cast("str | None", options.get("as_of")))
        created = 0

        for plan in EXAMPLE_LOAN_PLANS:
            edition = editions[plan.edition_index % len(editions)]
            copy = _ensure_copy(actor=actor, edition=edition, barcode=plan.barcode)
            if plan.is_returned:
                _sync_returned_loan(
                    actor=actor,
                    borrower=member,
                    copy=copy,
                    plan=plan,
                    anchor=anchor,
                )
            else:
                _sync_active_loan(
                    actor=actor,
                    borrower=member,
                    copy=copy,
                    plan=plan,
                    anchor=anchor,
                )
            created += 1

        history_copy_count, history_loan_count = _seed_background_history(
            actor=actor,
            editions=editions,
            borrowers=borrowers,
            anchor=anchor,
        )

        mode = "Refreshed" if bool(options["refresh"]) else "Seeded"
        detail = (
            f"{mode} {created} circulation example(s), {history_loan_count} historical loan(s), "
            f"and {history_copy_count} history copy/copies."
        )
        self.stdout.write(self.style.SUCCESS(detail))
