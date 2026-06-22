"""Create or refresh the disposable demo users."""

from __future__ import annotations

import os
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError

from libraryops.accounts.roles import ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER

# cspell:ignore Okafor Hana Mori Karim Hassan
DEMO_ACCESS_CODE_ENV_VAR = "LIBRARYOPS_DEMO_ACCESS_CODE"
DEMO_USERS = (
    ("admin@libraryops.demo", ROLE_ADMIN, True, True),
    ("librarian@libraryops.demo", ROLE_LIBRARIAN, True, False),
    ("member@libraryops.demo", ROLE_MEMBER, False, False),
)
DEMO_USER_NAMES = {
    "admin@libraryops.demo": ("Alex", "Morgan"),
    "librarian@libraryops.demo": ("Sam", "Rivera"),
    "member@libraryops.demo": ("Jamie", "Cole"),
}
DEMO_MEMBER_USERS = (
    ("ada.brooks@libraryops.demo", "Ada", "Brooks"),
    ("amelia.ward@libraryops.demo", "Amelia", "Ward"),
    ("benito.flores@libraryops.demo", "Benito", "Flores"),
    ("clara.nguyen@libraryops.demo", "Clara", "Nguyen"),
    ("darius.kim@libraryops.demo", "Darius", "Kim"),
    ("elena.singh@libraryops.demo", "Elena", "Singh"),
    ("felix.turner@libraryops.demo", "Felix", "Turner"),
    ("grace.okafor@libraryops.demo", "Grace", "Okafor"),
    ("hana.mori@libraryops.demo", "Hana", "Mori"),
    ("isaac.bennett@libraryops.demo", "Isaac", "Bennett"),
    ("jules.carter@libraryops.demo", "Jules", "Carter"),
    ("karim.hassan@libraryops.demo", "Karim", "Hassan"),
)


class Command(BaseCommand):
    """Seed the disposable demo accounts."""

    help = "Create the demo users and assign each one application role."

    def default_access_code(self) -> str:
        """Return the required disposable demo access code from the environment.

        Returns:
            The local disposable access code used when seeding demo users.

        Raises:
            CommandError: The local demo access-code environment variable is absent.
        """

        value = os.getenv(DEMO_ACCESS_CODE_ENV_VAR)
        if value is None or not value.strip():
            raise CommandError(
                f"Missing demo access code. Set `{DEMO_ACCESS_CODE_ENV_VAR}` before "
                "running `python manage.py seed_demo_users`."
            )
        return value

    def add_arguments(self, parser: Any) -> None:
        """Register command arguments.

        Args:
            parser: Django argument parser.
        """
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Reset the disposable demo user access code to the default value.",
        )

    def handle(self, *_args: str, **options: object) -> None:
        """Create or refresh the demo users."""
        default_access_code = self.default_access_code()
        missing_groups = [
            name
            for name in (ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER)
            if not Group.objects.filter(name=name).exists()
        ]
        if missing_groups:
            raise CommandError(
                "Missing role groups. Run `python manage.py seed_roles` before seeding demo users."
            )

        user_model = cast("type[User]", get_user_model())
        for email, role_name, is_staff, is_superuser in DEMO_USERS:
            first_name, last_name = DEMO_USER_NAMES.get(email, ("", ""))
            user, created = user_model.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if created or bool(options["reset_passwords"]):
                user.set_password(default_access_code)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.username = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            user_any = cast("Any", user)
            user_any.groups.set([Group.objects.get(name=role_name)])

        for email, first_name, last_name in DEMO_MEMBER_USERS:
            user, created = user_model.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if created or bool(options["reset_passwords"]):
                user.set_password(default_access_code)
            user.is_staff = False
            user.is_superuser = False
            user.username = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            user_any = cast("Any", user)
            user_any.groups.set([Group.objects.get(name=ROLE_MEMBER)])

        self.stdout.write(self.style.SUCCESS("Seeded disposable demo users."))
