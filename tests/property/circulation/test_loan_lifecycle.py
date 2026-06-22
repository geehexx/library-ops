"""Model-based properties for circulation transitions and DB constraints.

Each generated command maps to exactly one call to the public loan manager.  A
small reference model records the expected active/closed loan IDs, and the test
compares that model with the database after every step.  Rejected commands are
therefore checked for *non-mutation*, not merely for the expected exception.

A command-list property is preferable to a rule-based state machine here: the
surface has only three actions, list shrinking is especially transparent, and
there is no bundle or multi-object routing that would justify the extra state
machine machinery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from enum import StrEnum, auto

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from hypothesis import event, example, given, settings, target
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisDjangoTestCase

from libraryops.catalog.models import BibliographicWork, BookEdition
from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy, BookCopyStatus

pytestmark = pytest.mark.property


class LoanCommand(StrEnum):
    """Public circulation requests generated for a single copy."""

    CHECKOUT = auto()
    RETURN_CURRENT = auto()
    RETURN_CLOSED = auto()


@dataclass(slots=True)
class LoanReferenceModel:
    """Record expected state independently of manager/model helper properties."""

    active_loan_id: int | None = None
    closed_loan_ids: set[int] = field(default_factory=set[int])
    successful_checkouts: int = 0
    successful_returns: int = 0


def _saved_id(value: Loan | BookCopy | BookEdition | BibliographicWork | User) -> int:
    """Return a persisted primary key and fail clearly for unsaved fixtures."""
    assert value.pk is not None
    return int(value.pk)


class TestLoanLifecycleProperties(HypothesisDjangoTestCase):
    """Exercise accepted and rejected traces against a reference model."""

    @staticmethod
    def _make_graph() -> tuple[User, User, BookCopy, Loan]:
        """Create a minimal authorized graph and one immutable closed-loan oracle."""
        actor = User.objects.create_superuser(
            username="property-actor",
            email="property-actor@example.test",
            password=None,
        )
        borrower = User.objects.create_user(
            username="property-borrower",
            email="property-borrower@example.test",
            password=None,
        )
        work = BibliographicWork.objects.create(title="Property loan work")
        edition = BookEdition.objects.create(work=work, isbn="9780306406157")
        copy = BookCopy.objects.create(
            edition=edition,
            barcode="PBT-LOAN-0001",
            status=BookCopyStatus.AVAILABLE,
        )

        now = timezone.now()
        checked_out_at = now - timedelta(days=14)
        historical_closed = Loan.objects.create(
            copy=copy,
            borrower=borrower,
            checked_out_at=checked_out_at,
            due_at=checked_out_at + timedelta(days=7),
            returned_at=checked_out_at + timedelta(days=3),
        )
        return actor, borrower, copy, historical_closed

    @staticmethod
    def _checkout(
        *,
        actor: User,
        borrower: User,
        copy: BookCopy,
        model: LoanReferenceModel,
    ) -> None:
        """Execute one checkout request and update the model only on success."""
        if model.active_loan_id is not None:
            with pytest.raises(ValidationError):
                Loan.objects.checkout_copy(actor=actor, copy=copy, borrower=borrower)
            return

        loan = Loan.objects.checkout_copy(actor=actor, copy=copy, borrower=borrower)
        model.active_loan_id = _saved_id(loan)
        model.successful_checkouts += 1

    @staticmethod
    def _return_current(
        *,
        actor: User,
        historical_closed: Loan,
        model: LoanReferenceModel,
    ) -> None:
        """Return the active loan, or prove that a closed loan cannot be returned."""
        if model.active_loan_id is None:
            with pytest.raises(ValidationError):
                Loan.objects.return_copy(actor=actor, loan=historical_closed)
            return

        loan = Loan.objects.get(pk=model.active_loan_id)
        returned = Loan.objects.return_copy(actor=actor, loan=loan)
        returned_id = _saved_id(returned)
        model.closed_loan_ids.add(returned_id)
        model.active_loan_id = None
        model.successful_returns += 1

    @staticmethod
    def _return_closed(*, actor: User, historical_closed: Loan) -> None:
        """Prove that an explicit repeat-return request cannot mutate state."""
        with pytest.raises(ValidationError):
            Loan.objects.return_copy(actor=actor, loan=historical_closed)

    @staticmethod
    def _assert_database_matches(copy: BookCopy, model: LoanReferenceModel) -> None:
        """Compare the complete persisted projection with the reference model."""
        copy.refresh_from_db()
        active_ids = {
            int(pk)
            for pk in Loan.objects.filter(copy=copy, returned_at__isnull=True).values_list(
                "pk", flat=True
            )
        }
        closed_ids = {
            int(pk)
            for pk in Loan.objects.filter(copy=copy, returned_at__isnull=False).values_list(
                "pk", flat=True
            )
        }
        expected_active = {model.active_loan_id} if model.active_loan_id is not None else set[int]()

        assert active_ids == expected_active
        assert closed_ids == model.closed_loan_ids
        assert len(active_ids) <= 1
        assert model.successful_returns <= model.successful_checkouts
        assert model.successful_checkouts - model.successful_returns == len(active_ids)
        assert Loan.objects.filter(copy=copy).count() == 1 + model.successful_checkouts
        assert len(closed_ids) == 1 + model.successful_returns

        expected_status = (
            BookCopyStatus.ON_LOAN if model.active_loan_id is not None else BookCopyStatus.AVAILABLE
        )
        assert copy.status == expected_status

    @example(commands=[LoanCommand.CHECKOUT, LoanCommand.CHECKOUT])
    @example(commands=[LoanCommand.RETURN_CURRENT])
    @example(
        commands=[
            LoanCommand.CHECKOUT,
            LoanCommand.RETURN_CURRENT,
            LoanCommand.RETURN_CURRENT,
        ]
    )
    @settings(deadline=None)
    @given(
        commands=st.lists(
            st.sampled_from(tuple(LoanCommand)),
            min_size=1,
            max_size=12,
        )
    )
    def test_generated_command_traces_preserve_all_loan_invariants(
        self,
        commands: list[LoanCommand],
    ) -> None:
        """Accepted and rejected requests must preserve the complete loan projection."""
        actor, borrower, copy, historical_closed = self._make_graph()
        model = LoanReferenceModel(closed_loan_ids={_saved_id(historical_closed)})

        for command in commands:
            event(f"command={command.value}")

            if command is LoanCommand.CHECKOUT:
                self._checkout(actor=actor, borrower=borrower, copy=copy, model=model)
            elif command is LoanCommand.RETURN_CURRENT:
                self._return_current(
                    actor=actor,
                    historical_closed=historical_closed,
                    model=model,
                )
            else:
                self._return_closed(actor=actor, historical_closed=historical_closed)

            self._assert_database_matches(copy, model)

        target(model.successful_checkouts, label="successful_checkouts")
        target(model.successful_returns, label="successful_returns")
        event(f"terminal_active={model.active_loan_id is not None}")

    @settings(deadline=None)
    @given(history_size=st.integers(min_value=0, max_value=12))
    def test_partial_unique_constraint_allows_history_but_only_one_active_loan(
        self,
        history_size: int,
    ) -> None:
        """Returned history must neither consume nor weaken the one-active slot."""
        _, borrower, copy, _ = self._make_graph()
        now = timezone.now()

        # The graph contains one closed row already; add arbitrary additional history.
        for index in range(history_size):
            checked_out_at = now - timedelta(days=index + 30)
            Loan.objects.create(
                copy=copy,
                borrower=borrower,
                checked_out_at=checked_out_at,
                due_at=checked_out_at + timedelta(days=7),
                returned_at=checked_out_at + timedelta(days=2),
            )

        active = Loan.objects.create(copy=copy, borrower=borrower)
        with pytest.raises(IntegrityError), transaction.atomic():
            Loan.objects.create(copy=copy, borrower=borrower)

        assert Loan.objects.filter(copy=copy, returned_at__isnull=True).count() == 1
        assert Loan.objects.filter(copy=copy, returned_at__isnull=False).count() == history_size + 1

        active.returned_at = now
        active.save(update_fields=("returned_at",))
        replacement = Loan.objects.create(copy=copy, borrower=borrower)

        assert replacement.returned_at is None
        assert Loan.objects.filter(copy=copy, returned_at__isnull=True).count() == 1
        assert Loan.objects.filter(copy=copy, returned_at__isnull=False).count() == history_size + 2
        target(history_size, label="additional_historical_loans")
