"""Smoke tests for the Render deployment blueprint."""

from __future__ import annotations

from pathlib import Path


def test_render_blueprint_defines_a_renderable_django_service() -> None:
    """Ensure the repo-tracked blueprint contains the deployment contract."""
    blueprint = Path(__file__).resolve().parents[2] / "render.yaml"
    contents = blueprint.read_text(encoding="utf-8")

    assert "type: web" in contents
    assert "runtime: python" in contents
    assert "name: library-ops" in contents
    assert "plan: free" in contents
    assert (
        "buildCommand: python -m pip install uv && uv sync --frozen --no-dev && "
        "uv run --no-sync python manage.py migrate --noinput && "
        "uv run --no-sync python manage.py collectstatic --noinput" in contents
    )
    assert "preDeployCommand" not in contents
    assert (
        "startCommand: uv run --no-sync python -m gunicorn "
        "libraryops.config.wsgi:application --bind 0.0.0.0:$PORT" in contents
    )
    assert "healthCheckPath: /health/" in contents
    assert "DJANGO_SETTINGS_MODULE" in contents
    assert "DJANGO_ALLOWED_HOSTS" in contents
    assert "DATABASE_URL" in contents
    assert "generateValue: true" in contents
