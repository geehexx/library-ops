"""Browser coverage for the public auth surface."""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

import pytest
from django.core.management import call_command
from playwright.sync_api import Page, expect
from tests.e2e.visual_regression import assert_visual_snapshot

from libraryops.accounts.management.commands.seed_demo_users import DEMO_ACCESS_CODE_ENV_VAR

if TYPE_CHECKING:
    from pytest_django.live_server_helper import LiveServer

DEMO_ACCESS_CODE = "library-ops-demo-access-code"


def _social_providers_enabled() -> bool:
    """Return whether both optional OAuth providers are enabled for this run."""

    required_env_vars = (
        "DJANGO_ALLAUTH_GOOGLE_CLIENT_ID",
        "DJANGO_ALLAUTH_GOOGLE_SECRET",
        "DJANGO_ALLAUTH_GITHUB_CLIENT_ID",
        "DJANGO_ALLAUTH_GITHUB_SECRET",
    )
    return all(os.getenv(name, "").strip() for name in required_env_vars)


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestAuthSurfaceE2E:
    """Exercise the visible auth entry points with browser-backed checks."""

    def test_home_to_login_and_demo_sign_in(
        self,
        live_server: LiveServer,
        monkeypatch: pytest.MonkeyPatch,
        page: Page,
    ) -> None:
        """Verify the default email/password path from the public home page."""

        call_command("seed_roles")
        monkeypatch.setenv(DEMO_ACCESS_CODE_ENV_VAR, DEMO_ACCESS_CODE)
        call_command("seed_demo_users", reset_passwords=True)

        page.goto(live_server.url)

        expect(page.get_by_role("heading", name="Library Dashboard")).to_be_visible()
        primary_nav = page.get_by_role("navigation", name="Primary")
        expect(primary_nav.get_by_role("link", name="Sign in")).to_be_visible()
        expect(
            page.get_by_role("main").get_by_role("link", name="Sign in to the demo")
        ).to_be_visible()
        assert_visual_snapshot(page, "auth_surface", "default/home.png")

        primary_nav.get_by_role("link", name="Sign in").click()
        expect(page).to_have_url(f"{live_server.url}/accounts/login/")
        expect(page.get_by_role("heading", name="Sign In")).to_be_visible()
        expect(page.locator('input[type="email"]')).to_be_visible()
        expect(page.locator('input[type="password"]')).to_be_visible()
        expect(page.get_by_role("button", name="Sign In")).to_be_visible()
        expect(
            page.get_by_text("Google and GitHub sign-in use optional OAuth credentials.")
        ).to_be_visible()
        if _social_providers_enabled():
            expect(
                page.get_by_role("heading", name="Continue with Google or GitHub")
            ).to_be_visible()
            expect(
                page.get_by_role("link", name=re.compile("Google", re.IGNORECASE))
            ).to_be_visible()
            expect(
                page.get_by_role("link", name=re.compile("GitHub", re.IGNORECASE))
            ).to_be_visible()
        else:
            expect(
                page.get_by_text(
                    "This deployment exposes password sign-in only. "
                    "Use the seeded demo password path above to continue."
                )
            ).to_be_visible()
            expect(
                page.get_by_role("heading", name="Optional OAuth providers")
            ).to_be_visible()
            expect(
                page.get_by_role("link", name=re.compile("Google", re.IGNORECASE))
            ).to_have_count(0)
            expect(
                page.get_by_role("link", name=re.compile("GitHub", re.IGNORECASE))
            ).to_have_count(0)
        assert_visual_snapshot(page, "auth_surface", "default/login.png")

        page.locator('input[type="email"]').fill("librarian@libraryops.demo")
        page.locator('input[type="password"]').fill(DEMO_ACCESS_CODE)
        page.get_by_role("button", name="Sign In").click()

        expect(page).to_have_url(f"{live_server.url}/")
        primary_nav = page.get_by_role("navigation", name="Primary")
        expect(primary_nav.get_by_role("link", name="Sign out")).to_be_visible()
        expect(primary_nav.get_by_role("link", name="Create foundation record")).to_be_visible()
        assert_visual_snapshot(page, "auth_surface", "default/signed-in.png")

    @pytest.mark.skipif(
        not _social_providers_enabled(),
        reason="Optional OAuth providers are enabled through env vars in a separate run.",
    )
    def test_login_page_surfaces_google_and_github_provider_links(
        self,
        live_server: LiveServer,
        page: Page,
    ) -> None:
        """Verify the login page exposes the provider-linked UI when configured."""

        page.goto(f"{live_server.url}/accounts/login/")

        expect(page.get_by_role("heading", name="Sign In")).to_be_visible()
        expect(
            page.get_by_role("heading", name="Continue with Google or GitHub")
        ).to_be_visible()
        expect(
            page.get_by_text("Google and GitHub sign-in use optional OAuth credentials.")
        ).to_be_visible()
        expect(page.get_by_role("link", name=re.compile("Google", re.IGNORECASE))).to_be_visible()
        expect(page.get_by_role("link", name=re.compile("GitHub", re.IGNORECASE))).to_be_visible()
        expect(page.locator('input[type="email"]')).to_be_visible()
        expect(page.locator('input[type="password"]')).to_be_visible()
        assert_visual_snapshot(page, "auth_surface", "providers/login.png")
