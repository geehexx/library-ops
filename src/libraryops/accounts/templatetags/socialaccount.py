"""Safe socialaccount template tags for the login surface.

This local library keeps the login template renderable when optional
``allauth.socialaccount`` apps are absent, while delegating to the upstream
allauth implementation when OAuth providers are configured.
"""

from __future__ import annotations

from typing import Any

from django import template
from django.conf import settings

register = template.Library()


def _socialaccount_enabled() -> bool:
    """Return whether the optional socialaccount app is installed."""

    return "allauth.socialaccount" in settings.INSTALLED_APPS


def _load_upstream() -> Any | None:
    """Import the upstream allauth tag library when it is available."""

    try:
        from allauth.socialaccount.templatetags import socialaccount as upstream
    except Exception:
        return None
    return upstream


@register.simple_tag(takes_context=True)
def get_providers(context: template.Context) -> list[Any]:
    """Return the configured provider list or an empty list when disabled."""

    if not _socialaccount_enabled():
        return []

    upstream = _load_upstream()
    if upstream is None:
        return []

    return upstream.get_providers(context)


@register.simple_tag(takes_context=True)
def provider_login_url(
    context: template.Context,
    provider: str,
    **params: Any,
) -> str:
    """Return a provider login URL or an empty string when disabled."""

    if not _socialaccount_enabled():
        return ""

    upstream = _load_upstream()
    if upstream is None:
        return ""

    return upstream.provider_login_url(context, provider, **params)
