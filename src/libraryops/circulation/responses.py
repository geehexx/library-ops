"""HTTP response helpers for circulation workflows."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect


def workflow_response(request: HttpRequest, redirect_url: str) -> HttpResponse:
    """Return a browser redirect or HTMX redirect for workflow submissions."""

    if getattr(request, "htmx", False):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = redirect_url
        return response
    return HttpResponseRedirect(redirect_url)
