"""Helpers for the evaluator-facing browser visual-regression baseline flow."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageChops, ImageOps

if TYPE_CHECKING:
    from playwright.sync_api import Page

ARTIFACT_ROOT = Path("output/playwright")
BASELINE_ROOT = Path(__file__).resolve().parent / "visual_baselines"
BASELINE_REFRESH_ENV = "PLAYWRIGHT_VISUAL_BASELINE_REFRESH"


def _refresh_baselines_enabled() -> bool:
    """Return whether this run should refresh tracked visual baselines."""

    return os.getenv(BASELINE_REFRESH_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _artifact_path(*parts: str) -> Path:
    """Return the runtime capture path for a browser artifact."""

    path = ARTIFACT_ROOT.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _baseline_path(*parts: str) -> Path:
    """Return the tracked baseline path for a browser artifact."""

    path = BASELINE_ROOT.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_diff_image(actual_path: Path, baseline_path: Path) -> Path:
    """Write a human-readable diff artifact and return its path."""

    diff_path = actual_path.with_name(f"{actual_path.stem}.diff.png")
    with Image.open(actual_path) as actual_image, Image.open(baseline_path) as baseline_image:
        actual_rgba = actual_image.convert("RGBA")
        baseline_rgba = baseline_image.convert("RGBA")
        if actual_rgba.size != baseline_rgba.size:
            canvas = Image.new(
                "RGBA",
                (
                    actual_rgba.width + baseline_rgba.width,
                    max(actual_rgba.height, baseline_rgba.height),
                ),
                "white",
            )
            canvas.paste(baseline_rgba, (0, 0))
            canvas.paste(actual_rgba, (baseline_rgba.width, 0))
            canvas.save(diff_path)
            return diff_path

        diff = ImageChops.difference(actual_rgba, baseline_rgba)
        ImageOps.autocontrast(diff).save(diff_path)
    return diff_path


def assert_visual_snapshot(
    page: Page, suite: str, filename: str, *, full_page: bool = True
) -> None:
    """Capture a screenshot, compare it to the tracked baseline, and fail on drift."""

    actual_path = _artifact_path(suite, filename)
    baseline_path = _baseline_path(suite, filename)

    page.screenshot(path=str(actual_path), full_page=full_page)

    if _refresh_baselines_enabled():
        shutil.copyfile(actual_path, baseline_path)
        return

    if not baseline_path.exists():
        raise AssertionError(
            f"Missing visual baseline: {baseline_path}. "
            f"Set {BASELINE_REFRESH_ENV}=1 to refresh it from the current capture."
        )

    with Image.open(actual_path) as actual_image, Image.open(baseline_path) as baseline_image:
        actual_rgba = actual_image.convert("RGBA")
        baseline_rgba = baseline_image.convert("RGBA")

        if actual_rgba.size != baseline_rgba.size:
            diff_path = _write_diff_image(actual_path, baseline_path)
            raise AssertionError(
                "Visual snapshot size changed: "
                f"actual={actual_rgba.size} baseline={baseline_rgba.size} "
                f"(actual={actual_path}, baseline={baseline_path}, diff={diff_path})"
            )

        diff = ImageChops.difference(actual_rgba, baseline_rgba)
        if diff.getbbox() is not None:
            diff_path = _write_diff_image(actual_path, baseline_path)
            raise AssertionError(
                "Visual snapshot drift detected: "
                f"actual={actual_path} baseline={baseline_path} diff={diff_path}"
            )
