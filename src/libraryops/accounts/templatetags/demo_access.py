"""Template tags for evaluator-facing demo readiness copy."""

from __future__ import annotations

from django import template

from libraryops.accounts.demo_state import demo_auth_ready as demo_accounts_ready

register = template.Library()


@register.simple_tag
def demo_auth_ready() -> bool:
    """Return whether seeded demo accounts are currently available."""

    return demo_accounts_ready()
