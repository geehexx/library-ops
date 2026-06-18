"""Browser smoke tests for the Phase 1 navigation surface."""

from collections.abc import Callable
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from playwright.sync_api import Page, expect
from pytest_django.live_server_helper import LiveServer
from tests.factories import LibrarianUserFactory, MemberUserFactory

ARTIFACT_ROOT = Path("output/playwright/navigation")


def _artifact_path(filename: str) -> Path:
    """Return the on-disk path for a navigation screenshot artifact."""

    path = ARTIFACT_ROOT / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestNavigationE2E:
    """Cover the evaluator-facing navigation and access-denied flows."""

    def test_primary_navigation_reaches_catalog_and_login(
        self,
        live_server: LiveServer,
        page: Page,
    ) -> None:
        """Verify the public nav reaches the catalog and login entry point."""

        page.goto(live_server.url)

        primary_nav = page.get_by_role("navigation", name="Primary")
        expect(page.get_by_role("heading", name="Foundation Dashboard")).to_be_visible()
        expect(primary_nav.get_by_role("link", name="Sign in")).to_be_visible()
        expect(primary_nav.get_by_role("link", name="Create foundation record")).to_have_count(0)

        primary_nav.get_by_role("link", name="Catalog").click()
        expect(page).to_have_url(f"{live_server.url}/catalog/")
        expect(page.get_by_role("heading", name="Catalog Foundation")).to_be_visible()

        page.get_by_role("navigation", name="Primary").get_by_role("link", name="Sign in").click()
        expect(page).to_have_url(f"{live_server.url}/accounts/login/")
        expect(page.get_by_role("heading", name="Sign In")).to_be_visible()

    def test_librarian_sees_create_flow_and_validation_errors(
        self,
        live_server: LiveServer,
        page: Page,
        login_to_live_server: Callable[[User], None],
    ) -> None:
        """Verify that a catalog manager can reach the create flow and see field errors."""

        call_command("seed_roles")
        librarian = LibrarianUserFactory()
        login_to_live_server(librarian)

        page.goto(live_server.url)

        primary_nav = page.get_by_role("navigation", name="Primary")
        expect(primary_nav.get_by_role("link", name="Create foundation record")).to_be_visible()
        expect(primary_nav.get_by_role("link", name="Sign out")).to_be_visible()

        primary_nav.get_by_role("link", name="Create foundation record").click()
        expect(page).to_have_url(f"{live_server.url}/catalog/create/")
        expect(page.get_by_role("heading", name="Create Foundation Record")).to_be_visible()
        expect(page.get_by_label("Work title")).to_be_visible()
        expect(page.get_by_label("Contributor name")).to_be_visible()
        expect(page.get_by_label("Contributor role")).to_be_visible()

        page.get_by_role("button", name="Create foundation record").click()
        expect(page.get_by_role("heading", name="Fix the highlighted fields")).to_be_visible()
        expect(
            page.locator("span.error").filter(has_text="This field is required.").first
        ).to_be_visible()

    def test_member_sees_denied_state_for_create_flow(
        self,
        live_server: LiveServer,
        page: Page,
        login_to_live_server: Callable[[User], None],
    ) -> None:
        """Verify that a member hitting the protected create flow sees the denied state."""

        call_command("seed_roles")
        member = MemberUserFactory()
        login_to_live_server(member)

        page.goto(f"{live_server.url}/catalog/create/")

        expect(page.get_by_role("heading", name="Access denied")).to_be_visible()
        expect(page.get_by_text("You do not have permission")).to_be_visible()
        expect(page.get_by_role("link", name="Browse catalog")).to_be_visible()
        page.screenshot(path=str(_artifact_path("denied/create-flow.png")), full_page=True)
