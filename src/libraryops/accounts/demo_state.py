"""Helpers for runtime demo-state truth in evaluator-facing surfaces."""

from __future__ import annotations

from django.contrib.auth import get_user_model

DEMO_USER_EMAILS = (
    "admin@libraryops.demo",
    "librarian@libraryops.demo",
    "member@libraryops.demo",
)


def demo_auth_ready() -> bool:
    """Return whether the seeded demo users currently exist."""

    user_model = get_user_model()
    return user_model.objects.filter(email__in=DEMO_USER_EMAILS).count() == len(DEMO_USER_EMAILS)


def demo_data_ready(work_count: int, copy_count: int) -> bool:
    """Return whether evaluator-visible demo catalog data is present."""

    return work_count > 0 and copy_count > 0
