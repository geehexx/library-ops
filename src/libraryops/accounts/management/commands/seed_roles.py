"""Create the durable application role groups."""

from __future__ import annotations

from typing import Any, cast

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from libraryops.accounts.roles import ROLE_ADMIN, iter_role_definitions


class Command(BaseCommand):
    """Seed the Admin, Librarian, and Member groups."""

    help = "Create the Admin, Librarian, and Member groups."

    def handle(self, *_args: str, **_options: str) -> None:
        """Create groups and attach the baseline permission sets."""
        for role_definition in iter_role_definitions():
            group, _ = Group.objects.get_or_create(name=role_definition.name)
            group_any = cast("Any", group)
            if role_definition.name == ROLE_ADMIN:
                group_any.permissions.set(Permission.objects.all())
                continue

            permissions = Permission.objects.filter(
                content_type__app_label__in={
                    permission_name.split(".", maxsplit=1)[0]
                    for permission_name in role_definition.global_permissions
                },
                codename__in={
                    permission_name.split(".", maxsplit=1)[1]
                    for permission_name in role_definition.global_permissions
                },
            )
            group_any.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS("Seeded Admin, Librarian, and Member groups."))
