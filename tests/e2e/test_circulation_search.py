"""Browser coverage for circulation workflows and exact-identifier search ranking."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.core.management import call_command
from playwright.sync_api import Page, expect
from tests.e2e.visual_regression import assert_visual_snapshot
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    MemberUserFactory,
    WorkContributorFactory,
    build_isbn13,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.auth.models import User
    from pytest_django.live_server_helper import LiveServer


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestCirculationAndSearchE2E:
    """Exercise evaluator-visible circulation and search flows in the browser."""

    def test_librarian_can_checkout_and_return_a_copy_in_the_browser(
        self,
        live_server: LiveServer,
        page: Page,
        login_to_live_server: Callable[[User], None],
    ) -> None:
        """Verify the checkout and return workflow updates the dashboard state."""

        call_command("seed_roles")
        librarian = LibrarianUserFactory(first_name="Grace", last_name="Hopper")
        member = MemberUserFactory(first_name="Ada", last_name="Lovelace")

        work_contributor = WorkContributorFactory(
            work__title="Browser Circulation Work",
            contributor__name="Browser Librarian",
        )
        edition = BookEditionFactory(
            work=work_contributor.work,
            isbn=build_isbn13(91),
            language="en",
        )
        copy = BookCopyFactory(edition=edition, barcode="BC-BROWSER-001")

        login_to_live_server(librarian)
        page.goto(f"{live_server.url}/circulation/")

        expect(page.get_by_role("heading", name="Circulation Dashboard")).to_be_visible()
        expect(page.get_by_text("No active loans are visible.")).to_be_visible()
        expect(page.get_by_text("No recent returns are visible.")).to_be_visible()

        page.get_by_role("link", name="Checkout copy").click()
        checkout_dialog = page.get_by_role("dialog", name="Checkout copy")
        expect(checkout_dialog).to_be_visible()
        expect(checkout_dialog.get_by_role("combobox", name="Copy:")).to_be_visible()
        expect(checkout_dialog.get_by_role("combobox", name="Borrower:")).to_be_visible()
        expect(
            checkout_dialog.get_by_text(
                "Search first, then choose from the filtered select lists below."
            )
        ).to_be_visible()
        assert_visual_snapshot(page, "circulation_search", "checkout-form.png")

        checkout_dialog.get_by_role("combobox", name="Copy:").select_option(
            label=f"{copy.barcode} · Browser Circulation Work"
        )
        checkout_dialog.get_by_role("combobox", name="Borrower:").select_option(
            label=f"Ada Lovelace (PATRON-{member.pk:04d})"
        )
        page.get_by_role("button", name="Checkout copy").click()

        expect(page).to_have_url(f"{live_server.url}/circulation/")
        expect(
            page.get_by_text("Visible loans: 1 Active: 1 Overdue: 0 Recent returns: 0")
        ).to_be_visible()
        expect(page.get_by_text("Browser Circulation Work")).to_be_visible()

        page.get_by_role("link", name="Return copy").click()
        return_dialog = page.get_by_role("dialog", name="Return copy")
        expect(return_dialog).to_be_visible()
        expect(return_dialog.get_by_role("combobox", name="Loan:")).to_be_visible()
        expect(
            return_dialog.get_by_text(
                "Search first, then choose from the filtered select lists below."
            )
        ).to_be_visible()
        return_dialog.get_by_role("combobox", name="Loan:").select_option(
            label=(
                f"BC-BROWSER-001 · Browser Circulation Work · Ada Lovelace (PATRON-{member.pk:04d})"
            )
        )
        page.get_by_role("button", name="Return copy").click()

        expect(page).to_have_url(f"{live_server.url}/circulation/")
        expect(
            page.get_by_text("Visible loans: 1 Active: 0 Overdue: 0 Recent returns: 1")
        ).to_be_visible()
        expect(page.get_by_text("Browser Circulation Work")).to_be_visible()
        expect(page.get_by_role("cell", name=member.email)).to_be_visible()
        assert_visual_snapshot(page, "circulation_search", "checkout-return-dashboard.png")

    def test_catalog_search_ranks_exact_isbn_hits_first_in_the_browser(
        self,
        live_server: LiveServer,
        page: Page,
    ) -> None:
        """Verify an exact ISBN hit outranks a title-text distractor in the UI."""

        exact_work = WorkContributorFactory(
            work__title="Exact Search Work",
            contributor__name="Exact Search Author",
        ).work
        exact_edition = BookEditionFactory(
            work=exact_work,
            isbn="9780141439518",
            language="en",
        )
        BookCopyFactory(edition=exact_edition, barcode="BC-SEARCH-001")

        distractor_work = WorkContributorFactory(
            work__title="Reference 9780141439518 BC-1001 OL1W",
            contributor__name="Reference Author",
        ).work
        distractor_edition = BookEditionFactory(
            work=distractor_work,
            isbn=build_isbn13(92),
            language="fr",
        )
        BookCopyFactory(edition=distractor_edition, barcode="BC-SEARCH-002")

        page.goto(f"{live_server.url}/catalog/?q=9780141439518")

        expect(page.get_by_role("heading", name="Catalog Foundation")).to_be_visible()
        status = page.get_by_role("status")
        expect(status).to_have_attribute("aria-live", "polite")
        expect(status).to_have_text('Showing 2 results for "9780141439518"')
        expect(page.get_by_text("Exact identifier hit")).to_be_visible()
        expect(page.get_by_text("Matched identifier: 9780141439518")).to_be_visible()
        expect(page.get_by_text("Availability: Available")).to_be_visible()
        expect(page.get_by_text("Match: Exact identifier match")).to_be_visible()

        results = page.locator("section.panel").nth(1).locator("li")
        expect(results).to_have_count(2)
        expect(results.nth(0)).to_contain_text("Exact Search Work")
        expect(results.nth(0)).to_contain_text("Exact identifier hit")
        expect(results.nth(0)).to_contain_text("Matched identifier: 9780141439518")
        expect(results.nth(0)).to_contain_text("Availability: Available")
        expect(results.nth(0)).to_contain_text("Match: Exact identifier match")
        expect(results.nth(1)).to_contain_text("Reference 9780141439518 BC-1001 OL1W")
        assert_visual_snapshot(page, "circulation_search", "exact-isbn-ranking.png")

        search_field = page.get_by_label("Search catalog")
        search_field.click()
        expect(search_field).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("button", name="Search")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("link", name="Clear")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("combobox", name="Availability")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("combobox", name="Contributor")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("combobox", name="Subject")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("combobox", name="Language")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("combobox", name="Source")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("main").get_by_role("link", name="Sign in")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("link", name="Exact Search Work")).to_be_focused()
        page.keyboard.press("Enter")

        expect(page).to_have_url(f"{live_server.url}/catalog/{exact_work.pk}/")
        expect(page.get_by_role("heading", name="Exact Search Work")).to_be_visible()
