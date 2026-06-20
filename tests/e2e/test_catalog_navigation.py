"""Browser smoke tests for the evaluator-facing catalog detail surface."""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from PIL import Image
from playwright.sync_api import Page, expect
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LibrarianUserFactory,
    MemberUserFactory,
    WorkContributorFactory,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.auth.models import User
    from pytest_django.live_server_helper import LiveServer


def _cover_upload(filename: str, format_name: str = "PNG") -> SimpleUploadedFile:
    """Build one small cover image for browser-visible tests."""

    buffer = BytesIO()
    Image.new("RGB", (8, 8), color=(88, 112, 168)).save(buffer, format=format_name)
    return SimpleUploadedFile(
        filename,
        buffer.getvalue(),
        content_type=f"image/{format_name.lower()}",
    )


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestCatalogNavigationE2E:
    """Cover the browser-visible catalog browse and detail experience."""

    def test_catalog_detail_exposes_read_view_and_manager_actions(
        self,
        live_server: LiveServer,
        page: Page,
        login_to_live_server: Callable[[User], None],
    ) -> None:
        """Verify member and librarian catalog detail surfaces stay role-aware."""

        call_command("seed_roles")
        work_contributor = WorkContributorFactory(
            work__title="The Left Hand of Darkness",
            contributor__name="Ursula K. Le Guin",
        )
        work = work_contributor.work
        edition = BookEditionFactory(
            work=work,
            isbn="9780441478125",
            publisher="Ace",
            publication_year=1969,
            language="en",
            cover_url="https://example.com/the-left-hand-of-darkness.jpg",
            cover_image=_cover_upload("left-hand.png"),
        )
        BookCopyFactory(edition=edition, barcode="BC-0441", shelf_location="A1")

        member = MemberUserFactory()
        login_to_live_server(member)

        page.goto(f"{live_server.url}/catalog/{work.pk}/")
        expect(page.get_by_role("heading", name="The Left Hand of Darkness")).to_be_visible()
        expect(page.get_by_text("Ursula K. Le Guin")).to_be_visible()
        expect(page.get_by_text("9780441478125")).to_be_visible()
        expect(page.get_by_text("BC-0441")).to_be_visible()
        expect(
            page.get_by_role("img", name="Cover preview for The Left Hand of Darkness")
        ).to_be_visible()
        expect(page.get_by_role("link", name="Back to catalog")).to_be_visible()
        expect(page.get_by_role("link", name="Edit work")).to_have_count(0)
        expect(page.locator("details.archive-confirm")).to_have_count(0)

        librarian = LibrarianUserFactory()
        login_to_live_server(librarian)

        page.goto(f"{live_server.url}/catalog/{work.pk}/")
        expect(page.get_by_role("link", name="Edit work")).to_be_visible()
        expect(page.locator("details.archive-confirm")).to_have_count(3)
        expect(page.get_by_role("link", name="Edit edition")).to_be_visible()
        expect(page.get_by_role("link", name="Add edition")).to_be_visible()

    def test_catalog_detail_archive_actions_require_confirmation(
        self,
        live_server: LiveServer,
        page: Page,
        login_to_live_server: Callable[[User], None],
    ) -> None:
        """Verify each archive control opens a deliberate confirm/cancel choice."""

        call_command("seed_roles")
        work_contributor = WorkContributorFactory(
            work__title="Archive Confirmation Work",
            contributor__name="Archive Confirmation Author",
        )
        work = work_contributor.work
        edition = BookEditionFactory(
            work=work,
            isbn="9780141439518",
            language="en",
        )
        copy = BookCopyFactory(edition=edition, barcode="BC-ARCHIVE-001")

        librarian = LibrarianUserFactory()
        login_to_live_server(librarian)

        page.goto(f"{live_server.url}/catalog/{work.pk}/")
        expect(page.locator("details.archive-confirm")).to_have_count(3)

        page.locator("details.archive-confirm").nth(0).locator("summary").click()
        expect(page.get_by_text(f'Archive "{work.title}"?')).to_be_visible()
        expect(
            page.get_by_text("This work will disappear from normal browse and search flows.")
        ).to_be_visible()
        expect(page.get_by_role("button", name="Yes, archive work")).to_be_visible()
        expect(page.get_by_role("link", name="Keep work")).to_be_visible()
        page.get_by_role("link", name="Keep work").click()
        expect(page).to_have_url(f"{live_server.url}/catalog/{work.pk}/")

        page.locator("details.archive-confirm").nth(1).locator("summary").click()
        expect(page.get_by_text(f"Archive edition {edition.isbn}?")).to_be_visible()
        expect(
            page.get_by_text("This edition will disappear from normal browse and search flows.")
        ).to_be_visible()
        expect(page.get_by_role("button", name="Yes, archive edition")).to_be_visible()
        expect(page.get_by_role("link", name="Keep edition")).to_be_visible()
        page.get_by_role("link", name="Keep edition").click()
        expect(page).to_have_url(f"{live_server.url}/catalog/{work.pk}/")

        page.locator("details.archive-confirm").nth(2).locator("summary").click()
        expect(page.get_by_text(f"Archive copy {copy.barcode}?")).to_be_visible()
        expect(
            page.get_by_text("This copy will disappear from normal browse and search flows.")
        ).to_be_visible()
        expect(page.get_by_role("button", name="Yes, archive copy")).to_be_visible()
        expect(page.get_by_role("link", name="Keep copy")).to_be_visible()
        page.get_by_role("button", name="Yes, archive copy").click()

        expect(page).to_have_url(f"{live_server.url}/catalog/{work.pk}/")
        expect(page.get_by_text(copy.barcode)).to_have_count(0)
