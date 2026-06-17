"""Smoke tests for the Render deployment blueprint."""

from __future__ import annotations

from pathlib import Path


def test_render_blueprint_defines_a_renderable_django_service() -> None:
    """Ensure the repo-tracked blueprint contains the deployment contract."""
    blueprint = Path(__file__).resolve().parents[2] / "render.yaml"
    contents = blueprint.read_text(encoding="utf-8")

    assert "type: web" in contents
    assert "runtime: python" in contents
    assert (
        "buildCommand: uv sync --frozen --no-dev && uv run python manage.py collectstatic --noinput"
        in contents
    )
    assert "preDeployCommand: uv run python manage.py migrate --noinput" in contents
    assert "startCommand: uv run gunicorn libraryops.config.wsgi:application" in contents
    assert "healthCheckPath: /health/" in contents
    assert "fromDatabase:" in contents
    assert "generateValue: true" in contents
