"""Smoke coverage for the root Django Ninja API surface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.test import Client


def test_api_docs_are_exposed(client: Client) -> None:
    """Ensure the Swagger UI is available at the evaluator-facing docs URL."""

    response = client.get("/api/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]


def test_api_openapi_schema_is_exposed(client: Client) -> None:
    """Ensure the OpenAPI schema is available at the evaluator-facing JSON URL."""

    response = client.get("/api/openapi.json")
    payload: dict[str, Any] = response.json()

    assert response.status_code == 200
    assert payload["openapi"] == "3.1.0"
    assert payload["info"]["title"] == "Library Ops API"
    assert payload["info"]["version"] == "0.1.0"
