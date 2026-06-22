"""Role-selecting signup helpers for social-account completion."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from allauth.socialaccount.forms import SignupForm as SocialSignupForm

from libraryops.accounts.signup import (
    RoleSelectingSignupFormMixin,
    build_application_role_field,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class RoleSelectingSocialSignupForm(RoleSelectingSignupFormMixin, SocialSignupForm):
    """Social signup completion form that also captures the application role."""

    role = build_application_role_field()

    def save(self, request: Any) -> User:
        """Save the user and persist the selected application role."""
        user = cast("User", super().save(request))
        self._save_application_role(user)
        return user
