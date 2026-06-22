"""Tests for role-selecting signup forms and role normalization."""

from __future__ import annotations

from typing import Any, cast
from unittest import skipUnless

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.management import call_command
from django.test import RequestFactory, TestCase

from libraryops.accounts.permissions import get_user_role
from libraryops.accounts.roles import ROLE_ADMIN, ROLE_LIBRARIAN, ROLE_MEMBER
from libraryops.accounts.signup import (
    APPLICATION_ROLE_CHOICES,
    RoleSelectingAccountSignupForm,
    assign_application_role,
)

if "allauth.socialaccount" in settings.INSTALLED_APPS:
    from allauth.socialaccount.models import SocialAccount, SocialLogin

    from libraryops.accounts.social_signup import RoleSelectingSocialSignupForm
else:
    SocialAccount = None  # type: ignore[assignment]
    SocialLogin = None  # type: ignore[assignment]
    RoleSelectingSocialSignupForm = None  # type: ignore[assignment]


def _add_session(request: Any) -> Any:
    """Attach a session to a request factory request for allauth save hooks."""

    from django.http import HttpResponse

    middleware = SessionMiddleware(lambda _request: HttpResponse())
    middleware.process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    return request


class SignupFormTests(TestCase):
    """Cover local signup role assignment and drift normalization."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed the committed role fixtures once for this test class."""
        call_command("seed_roles")

    def test_application_role_choices_follow_committed_roles(self) -> None:
        """The signup choice list should mirror the committed role definitions."""

        assert [choice[0] for choice in APPLICATION_ROLE_CHOICES] == [
            ROLE_ADMIN,
            ROLE_LIBRARIAN,
            ROLE_MEMBER,
        ]

    def test_local_signup_assigns_selected_role_group_only(self) -> None:
        """Local signup should create the user and attach one role group."""

        form: Any = RoleSelectingAccountSignupForm(
            data={
                "email": "librarian@example.com",
                "password1": "strong-password-123",
                "password2": "strong-password-123",
                "role": ROLE_LIBRARIAN,
            }
        )
        assert form.is_valid(), form.errors

        request = _add_session(RequestFactory().post("/accounts/signup/"))
        user: Any = form.save(request)

        assert list(user.groups.values_list("name", flat=True)) == [ROLE_LIBRARIAN]
        assert get_user_role(user) == ROLE_LIBRARIAN

    def test_assign_application_role_normalizes_existing_role_drift(self) -> None:
        """Existing multi-role drift should collapse to the chosen application role."""

        user_model: Any = get_user_model()
        user: Any = user_model.objects.create_user(
            username="drifted",
            email="drifted@example.com",
            password="password-123",
        )
        support_group = Group.objects.create(name="Support")
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        librarian_group = Group.objects.get(name=ROLE_LIBRARIAN)
        user.groups.add(admin_group, librarian_group, support_group)

        assign_application_role(user, ROLE_MEMBER)

        assert sorted(user.groups.values_list("name", flat=True)) == [
            ROLE_MEMBER,
            "Support",
        ]
        assert get_user_role(user) == ROLE_MEMBER

    @skipUnless(
        "allauth.socialaccount" in settings.INSTALLED_APPS,
        "socialaccount tests are skipped when OAuth providers are disabled",
    )
    def test_social_signup_assigns_selected_role_group_only(self) -> None:
        """Social signup completion should also attach one role group."""

        social_login_cls = cast("Any", SocialLogin)
        social_account_cls = cast("Any", SocialAccount)
        social_signup_form_cls = cast("Any", RoleSelectingSocialSignupForm)
        user_model = get_user_model()
        sociallogin: Any = social_login_cls(
            user=user_model(),
            account=social_account_cls(provider="google", uid="google-uid"),
        )
        form: Any = social_signup_form_cls(
            sociallogin=sociallogin,
            data={
                "email": "member@example.com",
                "role": ROLE_MEMBER,
            },
        )
        assert form.is_valid(), form.errors

        request = _add_session(RequestFactory().post("/accounts/social/signup/"))
        user: Any = form.save(request)

        assert list(user.groups.values_list("name", flat=True)) == [ROLE_MEMBER]
        assert get_user_role(user) == ROLE_MEMBER
