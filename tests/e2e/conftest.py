"""Shared fixtures for Playwright-backed evaluator-flow tests."""

import os
from collections.abc import Callable

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from playwright.sync_api import Page
from pytest_django.live_server_helper import LiveServer

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture
def login_to_live_server(
    client: Client,
    live_server: LiveServer,
    page: Page,
) -> Callable[[User], None]:
    """Return a helper that transfers a Django session into the browser page."""

    def _login(user: User) -> None:
        client.force_login(user)
        session_cookie = client.cookies[settings.SESSION_COOKIE_NAME].value
        page.context.add_cookies(
            [
                {
                    "name": settings.SESSION_COOKIE_NAME,
                    "value": session_cookie,
                    "url": live_server.url,
                }
            ]
        )

    return _login
