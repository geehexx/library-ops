"""Tests for the circulation example seed command."""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from libraryops.accounts.management.commands.seed_demo_users import DEMO_ACCESS_CODE_ENV_VAR
from libraryops.catalog.management.commands.import_public_domain_catalog import (
    SOURCE_GUTENBERG,
    SOURCE_OPENLIBRARY,
)
from libraryops.circulation.management.commands.seed_circulation_examples import (
    EXAMPLE_ACTOR_EMAILS,
    EXAMPLE_LOAN_PLANS,
    EXAMPLE_MEMBER_EMAIL,
)
from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy, BookCopyStatus

TEST_DEMO_ACCESS_CODE = "library-ops-demo-access-code"


class SeedCirculationExamplesCommandTests(TestCase):
    """Cover the reproducible circulation snapshot command."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed the prerequisite roles, demo users, and catalog records."""

        call_command("seed_roles")

        original_demo_access_code = os.environ.get(DEMO_ACCESS_CODE_ENV_VAR)
        os.environ[DEMO_ACCESS_CODE_ENV_VAR] = TEST_DEMO_ACCESS_CODE
        try:
            call_command("seed_demo_users", reset_passwords=True)
        finally:
            if original_demo_access_code is None:
                os.environ.pop(DEMO_ACCESS_CODE_ENV_VAR, None)
            else:
                os.environ[DEMO_ACCESS_CODE_ENV_VAR] = original_demo_access_code

        call_command("import_public_domain_catalog", source=SOURCE_OPENLIBRARY, limit=1)
        call_command("import_public_domain_catalog", source=SOURCE_GUTENBERG, limit=1)

    def _assert_example_snapshot(self) -> None:
        """Assert the command produced the expected circulation states."""

        assert BookCopy.objects.filter(
            barcode__in=[plan.barcode for plan in EXAMPLE_LOAN_PLANS]
        ).count() == len(EXAMPLE_LOAN_PLANS)
        assert Loan.objects.count() == len(EXAMPLE_LOAN_PLANS)

        now = timezone.now()
        for plan in EXAMPLE_LOAN_PLANS:
            copy = BookCopy.objects.select_related("edition").get(barcode=plan.barcode)
            loan = Loan.objects.select_related("copy", "borrower").get(copy=copy)
            borrower = cast("Any", loan.borrower)
            assert borrower.email == EXAMPLE_MEMBER_EMAIL
            if plan.returned_days_ago is None:
                assert loan.returned_at is None
                assert copy.status == BookCopyStatus.ON_LOAN.value
                if plan.due_in_days >= 0:
                    assert loan.due_at > now
                else:
                    assert loan.due_at < now
                continue
            assert loan.returned_at is not None
            assert copy.status == BookCopyStatus.AVAILABLE.value
            assert loan.returned_at < now
            assert loan.due_at < now

        assert get_user_model().objects.filter(email__in=EXAMPLE_ACTOR_EMAILS).count() == len(
            EXAMPLE_ACTOR_EMAILS
        )

    def test_seed_command_is_idempotent_and_creates_realistic_states(self) -> None:
        """The command should create one active, one overdue, and one returned loan."""

        call_command("seed_circulation_examples")
        first_snapshot = {
            plan.barcode: Loan.objects.get(copy__barcode=plan.barcode).pk
            for plan in EXAMPLE_LOAN_PLANS
        }

        call_command("seed_circulation_examples")

        self._assert_example_snapshot()
        second_snapshot = {
            plan.barcode: Loan.objects.get(copy__barcode=plan.barcode).pk
            for plan in EXAMPLE_LOAN_PLANS
        }
        assert first_snapshot == second_snapshot

    def test_refresh_rebuilds_the_demo_snapshot_without_duplicates(self) -> None:
        """Refresh should restore the fixed example state even after drift."""

        call_command("seed_circulation_examples")

        tampered_copy = BookCopy.objects.get(barcode=EXAMPLE_LOAN_PLANS[0].barcode)
        Loan.objects.filter(copy=tampered_copy).update(due_at=timezone.now() - timedelta(days=30))

        call_command("seed_circulation_examples", refresh=True)

        self._assert_example_snapshot()
