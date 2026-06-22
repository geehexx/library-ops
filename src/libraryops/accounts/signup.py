"""Role-selecting signup helpers for allauth account signup."""

from __future__ import annotations

from typing import Any, Final, cast

from allauth.account.forms import SignupForm as AccountSignupForm
from django import forms
from django.contrib.auth.models import Group, User

from libraryops.accounts.roles import ROLE_DEFINITIONS, ROLE_NAMES

APPLICATION_ROLE_CHOICES: Final[tuple[tuple[str, str], ...]] = tuple(
    (role_definition.name, role_definition.name) for role_definition in ROLE_DEFINITIONS
)
APPLICATION_ROLE_HELP_TEXT: Final[str] = (
    "Choose exactly one application role. Library Ops uses that role group for permissions."
)


def build_application_role_field() -> forms.ChoiceField:
    """Build a reusable application-role field for signup forms."""

    return forms.ChoiceField(
        choices=APPLICATION_ROLE_CHOICES,
        help_text=APPLICATION_ROLE_HELP_TEXT,
        label="Application role",
    )


def _application_role_group(role_name: str) -> Group:
    """Return the committed role group for a signup choice."""

    return Group.objects.get(name=role_name)


def assign_application_role(user: User, role_name: str) -> None:
    """Normalize the user to exactly one application role group."""

    role_group = _application_role_group(role_name)
    user_any = cast("Any", user)
    existing_role_groups = list(user_any.groups.filter(name__in=ROLE_NAMES))
    if existing_role_groups:
        user_any.groups.remove(*existing_role_groups)
    user_any.groups.add(role_group)


class RoleSelectingSignupFormMixin:
    """Add application-role selection to an allauth signup form."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self_any = cast("Any", self)
        self_any.order_fields(["role", *[name for name in self_any.fields if name != "role"]])

    def clean_role(self) -> str:
        """Reject signup if the chosen role has not been seeded."""

        self_any = cast("Any", self)
        role_name = cast("str", self_any.cleaned_data["role"])
        if not Group.objects.filter(name=role_name).exists():
            raise forms.ValidationError(
                "Application roles are not seeded yet. Ask an administrator to run "
                "`python manage.py seed_roles`."
            )
        return role_name

    def _save_application_role(self, user: User) -> None:
        """Assign the chosen role group after allauth creates the user."""

        self_any = cast("Any", self)
        assign_application_role(user, cast("str", self_any.cleaned_data["role"]))


class RoleSelectingAccountSignupForm(RoleSelectingSignupFormMixin, AccountSignupForm):
    """Local signup form that lets every new account choose a role."""

    role = build_application_role_field()

    def save(self, request: Any) -> User:
        """Save the user and persist the selected application role."""
        user = cast("User", super().save(request))
        self._save_application_role(user)
        return user
