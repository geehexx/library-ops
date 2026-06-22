"""Integration tests for the auth signup surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast
from unittest import skipUnless
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

if "allauth.socialaccount" in settings.INSTALLED_APPS:
    from allauth.socialaccount.templatetags import socialaccount as socialaccount_tags
else:
    socialaccount_tags = None  # type: ignore[assignment]


@dataclass(slots=True)
class _FakeProvider:
    """Minimal provider double for template-tag rendering tests."""

    id: str
    name: str
    uses_apps: bool = False
    login_calls: list[dict[str, Any]] = field(
        default_factory=lambda: cast("list[dict[str, Any]]", [])
    )

    def get_login_url(self, _request: Any, **kwargs: Any) -> str:
        """Return a predictable login URL and capture the call arguments."""

        self.login_calls.append(kwargs)
        return f"/accounts/{self.id}/login/"

    def media_js(self, _request: Any) -> str:
        """Return no extra media JS for the template tag helper."""

        return ""


class _FakeAdapter:
    """Minimal allauth adapter double with a configurable provider list."""

    def __init__(self, providers: list[_FakeProvider]) -> None:
        self._providers = {provider.id: provider for provider in providers}

    def list_providers(self, _request: Any) -> list[_FakeProvider]:
        """Return the configured provider set for the template tag under test."""

        return list(self._providers.values())

    def get_provider(self, _request: Any, provider: str) -> _FakeProvider:
        """Return one configured provider by identifier."""

        return self._providers[provider]


class SignupSurfaceTests(TestCase):
    """Check role selection and provider parity on the signup page."""

    def test_signup_page_shows_role_selection_without_oauth_providers(self) -> None:
        """The local signup page should render role selection in no-provider mode."""

        if socialaccount_tags is None:
            response = self.client.get(reverse("account_signup"))
        else:
            adapter = _FakeAdapter([])
            with patch.object(cast("Any", socialaccount_tags), "get_adapter", return_value=adapter):
                response = self.client.get(reverse("account_signup"))

        assert response.status_code == 200
        self.assertContains(response, "Create a local Library Ops account", status_code=200)
        self.assertContains(response, "Application role", status_code=200)
        self.assertContains(
            response,
            "Choose one application role now.",
            status_code=200,
        )
        self.assertContains(response, 'name="role"', status_code=200)
        self.assertNotContains(response, "Or use a third-party")
        self.assertContains(response, "Create account", status_code=200)
        self.assertContains(response, "Already have an account?", status_code=200)

    @skipUnless(
        "allauth.socialaccount" in settings.INSTALLED_APPS,
        "provider-enabled signup rendering is skipped when OAuth is disabled",
    )
    def test_signup_page_shows_social_buttons_when_providers_exist(self) -> None:
        """The signup page should surface provider links when providers are enabled."""

        google = _FakeProvider(id="google", name="Google")
        github = _FakeProvider(id="github", name="GitHub")
        adapter = _FakeAdapter([google, github])

        with patch.object(cast("Any", socialaccount_tags), "get_adapter", return_value=adapter):
            response = self.client.get(reverse("account_signup"))

        assert response.status_code == 200
        self.assertContains(response, "Or continue with a provider", status_code=200)
        self.assertContains(response, 'href="/accounts/google/login/"', status_code=200)
        self.assertContains(response, 'href="/accounts/github/login/"', status_code=200)
        assert google.login_calls == [{"process": "login"}]
        assert github.login_calls == [{"process": "login"}]
