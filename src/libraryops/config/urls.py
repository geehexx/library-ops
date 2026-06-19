"""Root URL configuration."""

from __future__ import annotations

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static  # pyright: ignore[reportUnknownVariableType]
from django.http import HttpRequest, HttpResponse
from django.urls import include, path


def health(_request: HttpRequest) -> HttpResponse:
    """Return a minimal health-check response for smoke tests and probes."""
    return HttpResponse(b"ok", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("health/", health, name="health"),
    path("", include("libraryops.shell.urls")),
    path("circulation/", include("libraryops.circulation.urls")),
    path("catalog/", include("libraryops.catalog.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
