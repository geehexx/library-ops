"""Property tests for circulation loan invariants."""

from __future__ import annotations

from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils import timezone
from hypothesis import given, settings
from hypothesis import strategies as st
from tests.factories import BookCopyFactory, LibrarianUserFactory, LoanFactory, MemberUserFactory

from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy, BookCopyStatus


@pytest.fixture(scope="module", autouse=True)
def _seed_roles(  # pyright: ignore[reportUnusedFunction]
    django_db_setup: object,
    django_db_blocker: Any,
) -> None:
    """Seed auth roles once for the module-scoped property tests."""

    _ = django_db_setup
    with django_db_blocker.unblock():
        call_command("seed_roles")


def _assert_copy_state(copy: BookCopy, active_loan: Loan | None) -> None:
    """Assert the copy status matches whether an active loan exists."""

    copy.refresh_from_db()
    expected_status = (
        BookCopyStatus.ON_LOAN.value if active_loan is not None else BookCopyStatus.AVAILABLE.value
    )
    assert copy.status == expected_status
    assert Loan.objects.filter(copy=copy, returned_at__isnull=True).count() == (
        1 if active_loan is not None else 0
    )


@pytest.mark.django_db
@pytest.mark.property
@settings(max_examples=12, deadline=None)
@given(st.lists(st.booleans(), min_size=1, max_size=6))
def test_checkout_and_return_keep_copy_state_consistent(operation_pattern: list[bool]) -> None:
    """Generated checkout/return sequences should preserve copy and loan consistency."""

    actor = LibrarianUserFactory()
    borrower = MemberUserFactory()
    copy = BookCopyFactory()
    active_loan: Loan | None = None
    closed_loan: Loan | None = None

    _assert_copy_state(copy, active_loan)

    for checkout_attempt in operation_pattern:
        if checkout_attempt:
            if active_loan is None:
                active_loan = Loan.objects.checkout_copy(actor=actor, copy=copy, borrower=borrower)
            else:
                with pytest.raises(ValidationError):
                    Loan.objects.checkout_copy(actor=actor, copy=copy, borrower=borrower)
        else:
            if active_loan is None:
                if closed_loan is None:
                    closed_loan = LoanFactory(
                        copy=copy,
                        borrower=borrower,
                        returned_at=timezone.now(),
                    )
                with pytest.raises(ValidationError):
                    Loan.objects.return_copy(actor=actor, loan=closed_loan)
            else:
                closed_loan = Loan.objects.return_copy(actor=actor, loan=active_loan)
                active_loan = None

        _assert_copy_state(copy, active_loan)
