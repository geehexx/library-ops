"""Register opt-in Hypothesis profiles without replacing built-in defaults.

Hypothesis 6.155 provides built-in ``default`` and ``ci`` profiles. The CI
profile is selected automatically in recognized CI environments, so this file
only adds two explicit developer modes:

- ``quick`` reduces the example budget for a narrow edit/debug loop.
- ``deep`` increases the budget for an intentional pre-release or bug hunt.

Set ``HYPOTHESIS_PROFILE`` to select either custom profile. When the variable is
absent, Hypothesis retains its own current default or auto-selected CI profile.
"""

from __future__ import annotations

import os

from hypothesis import settings

settings.register_profile(
    "quick",
    parent=settings.get_profile("default"),
    max_examples=25,
)
settings.register_profile(
    "deep",
    parent=settings.get_profile("default"),
    max_examples=1_000,
    deadline=None,
    print_blob=True,
)

_requested_profile = os.environ.get("HYPOTHESIS_PROFILE")
if _requested_profile:
    settings.load_profile(_requested_profile)
