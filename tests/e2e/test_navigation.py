"""Browser smoke tests for the Phase 1 navigation surface."""

from collections.abc import Callable

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from playwright.sync_api import Page, expect
from pytest_django.live_server_helper import LiveServer
from tests.e2e.visual_regression import assert_visual_snapshot
from tests.factories import AdminUserFactory, LibrarianUserFactory, MemberUserFactory


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
        expect(page.get_by_role("heading", name="Library Dashboard")).to_be_visible()
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

    def test_librarian_can_open_the_loan_dashboard(
        self,
        live_server: LiveServer,
        page: Page,
        login_to_live_server: Callable[[User], None],
    ) -> None:
        """Verify the authenticated navigation exposes the circulation dashboard."""

        call_command("seed_roles")
        librarian = LibrarianUserFactory()
        login_to_live_server(librarian)

        page.goto(live_server.url)

        primary_nav = page.get_by_role("navigation", name="Primary")
        expect(primary_nav.get_by_role("link", name="Loans")).to_be_visible()
        primary_nav.get_by_role("link", name="Loans").click()

        expect(page).to_have_url(f"{live_server.url}/circulation/")
        expect(page.get_by_role("heading", name="Circulation Dashboard")).to_be_visible()

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
        expect(page.get_by_text("You do not have access to this page.")).to_be_visible()
        expect(page.get_by_role("link", name="Return home")).to_be_visible()
        assert_visual_snapshot(page, "navigation", "denied/create-flow.png")

    def test_admin_user_can_reach_django_admin_index(
        self,
        live_server: LiveServer,
        page: Page,
        login_to_live_server: Callable[[User], None],
    ) -> None:
        """Verify a superuser can reach the Django admin index route."""

        admin = AdminUserFactory()
        login_to_live_server(admin)

        page.goto(f"{live_server.url}/admin/")

        expect(page).to_have_url(f"{live_server.url}/admin/")
        expect(page.get_by_role("heading", name="Site administration")).to_be_visible()

    def test_health_route_is_browser_visible_and_returns_plain_ok(
        self,
        live_server: LiveServer,
        page: Page,
    ) -> None:
        """Verify /health/ is reachable in-browser and returns the plain-text sentinel."""

        page.goto(f"{live_server.url}/health/")

        expect(page).to_have_url(f"{live_server.url}/health/")
        expect(page.locator("body")).to_have_text("ok")
