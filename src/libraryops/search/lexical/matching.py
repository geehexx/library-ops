"""Exact phrase and portable broad-match expressions.

PostgreSQL full-text ranking is implemented by a backend strategy. This module
owns the deterministic phrase signals shared by every backend and the SQLite-
safe fallback used when PostgreSQL search functions are unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db.models import BooleanField, Case, Exists, OuterRef, Q, Value, When

from libraryops.catalog.models import BookEdition, WorkContributor

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from .criteria import SearchTerm


def _false_expression() -> Combinable:
    """Return a database-portable boolean false expression."""

    return Value(False, output_field=BooleanField())


@dataclass(frozen=True, slots=True)
class TextMatchBuilder:
    """Build exact-phrase and cross-field portable lexical signals."""

    def aliases(self, term: SearchTerm) -> dict[str, Combinable]:
        """Return private aliases for all text-match signals.

        Args:
            term: Normalized user query.

        Returns:
            Exact title, exact contributor, and portable broad-match
            expressions.
        """

        return {
            "_search_title_phrase_hit": self._title_phrase_hit(term),
            "_search_contributor_phrase_hit": self._contributor_phrase_hit(term),
            "_search_broad_hit": self._broad_hit(term),
        }

    @staticmethod
    def _title_phrase_hit(term: SearchTerm) -> Combinable:
        """Return exact normalized-title equality.

        Args:
            term: Normalized user query.

        Returns:
            A boolean ``CASE`` expression. Queries containing no normalizable
            text cannot match a blank normalized title accidentally.
        """

        if not term.normalized_phrase:
            return _false_expression()
        return Case(
            When(normalized_title=term.normalized_phrase, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )

    @staticmethod
    def _contributor_phrase_hit(term: SearchTerm) -> Combinable:
        """Return exact normalized-contributor equality.

        Args:
            term: Normalized user query.

        Returns:
            A correlated existence expression.
        """

        if not term.normalized_phrase:
            return _false_expression()
        relations = WorkContributor.objects.filter(
            work_id=OuterRef("pk"),
            contributor__normalized_name=term.normalized_phrase,
        ).order_by()
        return Exists(relations)

    def _broad_hit(self, term: SearchTerm) -> Combinable:
        """Return a portable all-token match across searchable fields.

        Every token must occur in at least one work, contributor, publisher,
        edition description, or edition metadata field. This approximates
        PostgreSQL web-search ``AND`` semantics while remaining SQLite-safe.

        Args:
            term: Normalized user query.

        Returns:
            A boolean ``CASE`` expression.
        """

        if not term.tokens:
            return _false_expression()
        condition = Q()
        for token in term.tokens:
            condition &= self._token_condition(token)
        return Case(
            When(condition, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )

    @staticmethod
    def _token_condition(token: str) -> Q:
        """Return a cross-field condition for one fallback token.

        Args:
            token: One normalized Unicode word token.

        Returns:
            A disjunction spanning work, contributor, and active-edition text.
        """

        contributor_match = WorkContributor.objects.filter(
            work_id=OuterRef("pk"),
            contributor__normalized_name__contains=token,
        ).order_by()
        edition_match = (
            BookEdition.objects.filter(
                work_id=OuterRef("pk"),
                archived_at__isnull=True,
            )
            .filter(
                Q(publisher__icontains=token)
                | Q(description__icontains=token)
                | Q(external_identifiers__icontains=token)
            )
            .order_by()
        )
        return (
            Q(normalized_title__contains=token)
            | Q(description__icontains=token)
            | Q(Exists(contributor_match))
            | Q(Exists(edition_match))
        )


def any_phrase_hit_expression() -> Case:
    """Return one boolean expression combining title and contributor aliases."""

    return Case(
        When(_search_title_phrase_hit=True, then=Value(True)),
        When(_search_contributor_phrase_hit=True, then=Value(True)),
        default=Value(False),
        output_field=BooleanField(),
    )
