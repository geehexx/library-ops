"""Create or refresh the disposable demo users."""

from __future__ import annotations

from typing import Any, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError

from libraryops.accounts.roles import ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER

DEFAULT_PASSWORD = "LibraryOpsDemo123!"
DEMO_USERS = (
    ("admin@libraryops.demo", ROLE_ADMIN, True, True),
    ("librarian@libraryops.demo", ROLE_LIBRARIAN, True, False),
    ("member@libraryops.demo", ROLE_MEMBER, False, False),
)


class Command(BaseCommand):
    """Seed the disposable demo accounts."""

    help = "Create the demo users and assign each one application role."

    def add_arguments(self, parser: Any) -> None:
        """Register command arguments.

        Args:
            parser: Django argument parser.
        """
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Reset the disposable demo user passwords to the default value.",
        )

    def handle(self, *_args: str, **options: object) -> None:
        """Create or refresh the demo users."""
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
            user, created = user_model.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                },
            )
            if created or bool(options["reset_passwords"]):
                user.set_password(DEFAULT_PASSWORD)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.username = email
            user.save()
            user_any = cast("Any", user)
            user_any.groups.set([Group.objects.get(name=role_name)])

        self.stdout.write(self.style.SUCCESS("Seeded disposable demo users."))
