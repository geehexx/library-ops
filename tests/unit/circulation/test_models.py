"""Tests for circulation loan invariants."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
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
