"""Integration tests for the auth login surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast
from unittest import SkipTest
from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

if "allauth.socialaccount" in settings.INSTALLED_APPS:
    from allauth.socialaccount.templatetags import socialaccount as socialaccount_tags
else:
    raise SkipTest(
        "Optional socialaccount tests are skipped when OAuth providers are disabled."
    )


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
        query: dict[str, Any] = {}
        next_value = kwargs.get("next")
        if next_value:
            query["next"] = next_value
        query_string = urlencode(query)
        if query_string:
            return f"/accounts/{self.id}/login/?{query_string}"
        return f"/accounts/{self.id}/login/"


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


class LoginSurfaceTests(TestCase):
    """Check provider parity and redirect preservation on the login page."""

    def _render_login_page(
        self,
        providers: list[_FakeProvider],
        next_path: str | None = None,
    ):
        """Render the login page with a fake provider adapter."""

        adapter = _FakeAdapter(providers)
        with patch.object(socialaccount_tags, "get_adapter", return_value=adapter):
            request_args = {"next": next_path} if next_path is not None else {}
            response = self.client.get(reverse("account_login"), request_args)
        return response, providers

    def test_login_page_shows_no_provider_links_when_none_enabled(self) -> None:
        """The provider panel should fall back cleanly when no OAuth providers exist."""

        response, _providers = self._render_login_page([], next_path="/catalog/")

        assert response.status_code == 200
        self.assertContains(
            response,
            "This deployment exposes password sign-in only.",
            status_code=200,
        )
        self.assertContains(response, 'name="next"', status_code=200)
        self.assertContains(response, 'value="/catalog/"', status_code=200)
        self.assertNotContains(response, "Continue with Google")
        self.assertNotContains(response, "Continue with GitHub")

    def test_login_page_shows_only_one_provider_and_preserves_next(self) -> None:
        """A one-provider deployment should expose only the configured provider link."""

        google = _FakeProvider(id="google", name="Google")

        response, providers = self._render_login_page([google], next_path="/catalog/")

        assert response.status_code == 200
        self.assertContains(response, "Continue with Google", status_code=200)
        self.assertNotContains(response, "Continue with GitHub")
        self.assertContains(
            response,
            'href="/accounts/google/login/?next=%2Fcatalog%2F"',
            status_code=200,
        )
        self.assertContains(response, 'name="next"', status_code=200)
        self.assertContains(response, 'value="/catalog/"', status_code=200)
        assert providers[0].login_calls[-1]["process"] == "login"
        assert providers[0].login_calls[-1]["next"] == "/catalog/"

    def test_login_page_shows_both_enabled_providers(self) -> None:
        """A two-provider deployment should expose both configured provider links."""

        google = _FakeProvider(id="google", name="Google")
        github = _FakeProvider(id="github", name="GitHub")

        response, providers = self._render_login_page([google, github])

        assert response.status_code == 200
        self.assertContains(response, "Continue with GitHub", status_code=200)
        self.assertContains(response, "Continue with Google", status_code=200)
        self.assertContains(response, 'href="/accounts/github/login/"', status_code=200)
        self.assertContains(response, 'href="/accounts/google/login/"', status_code=200)
        assert providers[0].login_calls == [{"process": "login"}]
        assert providers[1].login_calls == [{"process": "login"}]
