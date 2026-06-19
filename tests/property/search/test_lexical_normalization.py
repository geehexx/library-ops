"""Property tests for lexical catalog search normalization."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from django.core.management import call_command
from hypothesis import given, settings
from hypothesis import strategies as st
from tests.factories import BookEditionFactory, WorkContributorFactory

from libraryops.search.lexical import search_catalog


@pytest.fixture(scope="module")
def search_case(django_db_setup: object, django_db_blocker: Any) -> tuple[int, str]:
    """Seed one searchable work that property examples can query repeatedly."""

    _ = django_db_setup
    token = uuid4().hex
    normalized_query = f"The Dispossessed {token}"

    with django_db_blocker.unblock():
        call_command("seed_roles")
        work = WorkContributorFactory(
            work__title=normalized_query,
            contributor__name=f"Ursula K. Le Guin {token}",
        ).work
        BookEditionFactory(work=work)

    return work.pk, normalized_query


@pytest.mark.django_db
@pytest.mark.property
@settings(max_examples=16, deadline=None)
@given(
    prefix=st.text(alphabet=" \t\n\r", min_size=0, max_size=3),
    middle_1=st.text(alphabet=" \t\n\r", min_size=1, max_size=3),
    middle_2=st.text(alphabet=" \t\n\r", min_size=1, max_size=3),
    suffix=st.text(alphabet=" \t\n\r", min_size=0, max_size=3),
)
def test_search_catalog_collapses_whitespace_idempotently(
    search_case: tuple[int, str],
    prefix: str,
    middle_1: str,
    middle_2: str,
    suffix: str,
) -> None:
    """Whitespace-only query noise should not change lexical search results."""

    work_pk, normalized_query = search_case
    token = normalized_query.rsplit(" ", maxsplit=1)[-1]
    noisy_query = f"{prefix}The{middle_1}Dispossessed{middle_2}{token}{suffix}"

    assert list(search_catalog(noisy_query).values_list("pk", flat=True)) == [work_pk]
    assert list(search_catalog(noisy_query).values_list("pk", flat=True)) == list(
        search_catalog(normalized_query).values_list("pk", flat=True)
    )
