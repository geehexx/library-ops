"""Application role definitions and permission bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

ROLE_ADMIN = "Admin"
ROLE_LIBRARIAN = "Librarian"
ROLE_MEMBER = "Member"
ROLE_NAMES = (ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER)

CATALOG_CREATE_PERMISSIONS: Final[tuple[str, ...]] = (
    "catalog.add_bibliographicwork",
    "catalog.add_bookedition",
    "inventory.add_bookcopy",
    "audit.add_auditevent",
)
LIBRARIAN_GLOBAL_PERMISSIONS: Final[tuple[str, ...]] = (
    *CATALOG_CREATE_PERMISSIONS,
    "catalog.view_bibliographicwork",
    "catalog.change_bibliographicwork",
    "catalog.view_bookedition",
    "catalog.change_bookedition",
    "inventory.view_bookcopy",
    "inventory.change_bookcopy",
    "circulation.view_loan",
    "circulation.change_loan",
    "audit.view_auditevent",
)
MEMBER_GLOBAL_PERMISSIONS: Final[tuple[str, ...]] = (
    "catalog.view_bibliographicwork",
    "catalog.view_bookedition",
    "inventory.view_bookcopy",
)
ADMIN_OBJECT_PERMISSIONS: Final[tuple[str, ...]] = (
    "catalog.view_bibliographicwork",
    "catalog.change_bibliographicwork",
    "catalog.view_bookedition",
    "catalog.change_bookedition",
    "inventory.view_bookcopy",
    "inventory.change_bookcopy",
    "audit.view_auditevent",
)
LIBRARIAN_OBJECT_PERMISSIONS: Final[tuple[str, ...]] = ADMIN_OBJECT_PERMISSIONS
MEMBER_OBJECT_PERMISSIONS: Final[tuple[str, ...]] = (
    "catalog.view_bibliographicwork",
    "catalog.view_bookedition",
    "inventory.view_bookcopy",
)


@dataclass(frozen=True, slots=True)
class RoleDefinition:
    """Describe one application role and its permission bundles."""

    name: str
    global_permissions: tuple[str, ...]
    object_permissions: tuple[str, ...]


ROLE_DEFINITIONS: Final[tuple[RoleDefinition, ...]] = (
    RoleDefinition(
        name=ROLE_ADMIN,
        global_permissions=(),
        object_permissions=ADMIN_OBJECT_PERMISSIONS,
    ),
    RoleDefinition(
        name=ROLE_LIBRARIAN,
        global_permissions=LIBRARIAN_GLOBAL_PERMISSIONS,
        object_permissions=LIBRARIAN_OBJECT_PERMISSIONS,
    ),
    RoleDefinition(
        name=ROLE_MEMBER,
        global_permissions=MEMBER_GLOBAL_PERMISSIONS,
        object_permissions=MEMBER_OBJECT_PERMISSIONS,
    ),
)


def iter_role_definitions() -> tuple[RoleDefinition, ...]:
    """Return the committed application role definitions."""

    return ROLE_DEFINITIONS


def resolve_role_name(group_names: set[str]) -> str | None:
    """Return the highest-priority application role found in a group-name set."""

    for role_name in ROLE_NAMES:
        if role_name in group_names:
            return role_name
    return None
