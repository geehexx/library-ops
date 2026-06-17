"""Tests for role and demo-user seeding commands."""

from __future__ import annotations

import os
from typing import Any, Protocol, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from libraryops.accounts.management.commands.seed_demo_users import (
    DEFAULT_PASSWORD_ENV_VAR,
    DEMO_USERS,
)
from libraryops.accounts.roles import ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER

TEST_DEMO_PASSWORD = "library-ops-demo-password"


class _PermissionGroupLike(Protocol):
    """Protocol for the minimal group shape used in assertions."""

    permissions: Any


class _SeedUserLike(Protocol):
    """Protocol for the seeded demo-user shape used in assertions."""

    is_staff: bool
    is_superuser: bool
    groups: Any

    def check_password(self, raw_password: str) -> bool:
        """Return whether the stored password matches the provided value."""
        ...


class SeedRolesCommandTests(TestCase):
    """Cover the durable application role groups."""

    def test_seed_roles_is_idempotent_and_limits_permissions(self) -> None:
        """Ensure the role seed command is stable and permission-scoped."""

        call_command("seed_roles")
        call_command("seed_roles")

        assert Group.objects.count() == 3

        admin_group = cast("_PermissionGroupLike", Group.objects.get(name=ROLE_ADMIN))
        librarian_group = cast("_PermissionGroupLike", Group.objects.get(name=ROLE_LIBRARIAN))
        member_group = cast("_PermissionGroupLike", Group.objects.get(name=ROLE_MEMBER))

        admin_permissions = list(admin_group.permissions.all())
        librarian_permissions = list(librarian_group.permissions.all())
        member_permissions = list(member_group.permissions.all())

        assert admin_permissions
        assert librarian_permissions
        assert member_permissions
        assert all(
            permission.content_type.app_label in {"catalog", "inventory", "circulation", "audit"}
            and permission.codename.startswith(("view_", "add_", "change_"))
            for permission in librarian_permissions
        )
        assert all(
            permission.content_type.app_label in {"catalog", "inventory"}
            and permission.codename.startswith("view_")
            for permission in member_permissions
        )


class SeedDemoUsersCommandTests(TestCase):
    """Cover the deterministic demo-user command."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed the durable role groups before creating demo users."""

        call_command("seed_roles")

    def setUp(self) -> None:
        """Set the required demo password env var for the command under test."""

        self.original_demo_password = os.environ.get(DEFAULT_PASSWORD_ENV_VAR)
        os.environ[DEFAULT_PASSWORD_ENV_VAR] = TEST_DEMO_PASSWORD

    def tearDown(self) -> None:
        """Restore the prior demo password env var after the test."""

        if self.original_demo_password is None:
            os.environ.pop(DEFAULT_PASSWORD_ENV_VAR, None)
            return
        os.environ[DEFAULT_PASSWORD_ENV_VAR] = self.original_demo_password

    def test_seed_demo_users_is_idempotent_and_assigns_roles(self) -> None:
        """Ensure the demo-user seed is stable and role-aware."""

        call_command("seed_demo_users", reset_passwords=True)
        call_command("seed_demo_users")

        user_model = get_user_model()
        assert user_model.objects.count() == len(DEMO_USERS)

        for email, role_name, is_staff, is_superuser in DEMO_USERS:
            user = cast("_SeedUserLike", user_model.objects.get(email=email))
            assert user.check_password(TEST_DEMO_PASSWORD)
            assert user.is_staff == is_staff
            assert user.is_superuser == is_superuser
            assert [group.name for group in user.groups.all()] == [role_name]
