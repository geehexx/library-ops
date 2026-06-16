"""Smoke tests for the committed Django bootstrap."""

from __future__ import annotations

from django.test import Client


def test_health_endpoint() -> None:
    """Verify that the health endpoint responds successfully."""
    response = Client().get("/health/")

    assert response.status_code == 200
    assert response.content == b"ok"
