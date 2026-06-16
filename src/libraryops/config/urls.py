"""Root URL configuration."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import path


def health(_request: HttpRequest) -> HttpResponse:
    """Return a minimal health-check response for smoke tests and probes."""
    return HttpResponse(b"ok", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
]
