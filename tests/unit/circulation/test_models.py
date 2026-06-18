"""Tests for circulation loan invariants."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from hypothesis import given, settings
from hypothesis import strategies as st
from tests.factories import BookCopyFactory, MemberUserFactory

from libraryops.circulation.models import Loan, default_due_at


class LoanModelTests(TestCase):
    """Cover due-date behavior and the one-active-loan invariant."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create the copy and borrower used by circulation tests."""

        cls.borrower = MemberUserFactory()
        cls.copy = BookCopyFactory()

    def test_due_at_uses_named_default_callable(self) -> None:
        """Ensure the default due date stays within the expected window."""

        due_at = default_due_at()
        delta = due_at - timezone.now()
        assert delta > timedelta(days=13)
        assert delta < timedelta(days=15)

    def test_only_one_active_loan_exists_per_copy(self) -> None:
        """Ensure a second active loan for one copy violates the DB constraint."""

        Loan.objects.create(copy=self.copy, borrower=self.borrower)

        with pytest.raises(IntegrityError):
            Loan.objects.create(copy=self.copy, borrower=self.borrower)


@pytest.mark.django_db
@pytest.mark.property
@settings(max_examples=10, deadline=None)
@given(st.lists(st.booleans(), min_size=1, max_size=5))
def test_active_loan_constraint_holds_across_return_patterns(return_pattern: list[bool]) -> None:
    """Ensure only one unreturned loan can exist even across mixed loan histories."""

    borrower = MemberUserFactory()
    copy = BookCopyFactory()
    active_loan_exists = False

    for is_returned in return_pattern:
        if is_returned:
            Loan.objects.create(copy=copy, borrower=borrower, returned_at=timezone.now())
            continue

        if active_loan_exists:
            with transaction.atomic(), pytest.raises(IntegrityError):
                Loan.objects.create(copy=copy, borrower=borrower)
            continue

        Loan.objects.create(copy=copy, borrower=borrower)
        active_loan_exists = True
