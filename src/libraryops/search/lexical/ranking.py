"""Deterministic exact-first ranking and public result annotations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING

from django.db.models import (
    Case,
    F,
    FloatField,
    IntegerField,
    Q,
    TextField,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce
from django.db.models.lookups import GreaterThan

from .identifiers import IdentifierMatchBuilder, any_identifier_hit_expression
from .matching import TextMatchBuilder, any_phrase_hit_expression

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from libraryops.catalog.models import BibliographicWork

    from .backends import KeywordRankBackend
    from .criteria import SearchTerm


class MatchTier(IntEnum):
    """Stable ordering tiers from strongest to weakest match."""

    EXACT_IDENTIFIER = 0
    EXACT_PHRASE = 1
    KEYWORD = 2
    BROAD_LEXICAL = 3


class MatchExplanation(StrEnum):
    """Human-readable explanations aligned one-to-one with ranking tiers."""

    EXACT_IDENTIFIER = "Exact identifier match"
    EXACT_PHRASE = "Exact phrase match"
    KEYWORD = "Keyword match"
    BROAD_LEXICAL = "Broad lexical match"


@dataclass(frozen=True, slots=True)
class DeterministicRankingPolicy:
    """Apply private match aliases, public annotations, and stable ordering.

    Intermediate signals use ``QuerySet.alias()`` so they can participate in
    filtering and ordering without widening every selected result row. Only the
    three annotations consumed by callers are selected:
    ``search_keyword_rank``, ``search_rank``, and ``search_explanation``.
    """

    identifiers: IdentifierMatchBuilder = field(default_factory=IdentifierMatchBuilder)
    text_matches: TextMatchBuilder = field(default_factory=TextMatchBuilder)

    def apply(
        self,
        queryset: QuerySet[BibliographicWork],
        term: SearchTerm,
        *,
        keyword_backend: KeywordRankBackend,
    ) -> QuerySet[BibliographicWork]:
        """Rank one non-empty lexical query.

        Args:
            queryset: Facet-filtered work queryset.
            term: Normalized non-empty query.
            keyword_backend: Database-specific relevance strategy.

        Returns:
            Matching works with public score, tier, and explanation
            annotations.
        """

        queryset = queryset.alias(
            **self.identifiers.aliases(term),
            **self.text_matches.aliases(term),
        )
        queryset = queryset.alias(
            _search_identifier_hit=any_identifier_hit_expression(),
            _search_phrase_hit=any_phrase_hit_expression(),
            _search_keyword_rank=Coalesce(
                Cast(keyword_backend.rank_expression(term), output_field=FloatField()),
                Value(0.0),
                output_field=FloatField(),
            ),
        )
        queryset = queryset.alias(
            _search_keyword_hit=GreaterThan(F("_search_keyword_rank"), Value(0.0)),
        )
        queryset = queryset.filter(
            Q(_search_identifier_hit=True)
            | Q(_search_phrase_hit=True)
            | Q(_search_keyword_hit=True)
            | Q(_search_broad_hit=True)
        )
        return queryset.annotate(
            search_keyword_rank=F("_search_keyword_rank"),
            search_rank=self._rank_expression(),
            search_explanation=self._explanation_expression(),
        ).order_by(
            "search_rank",
            "-search_keyword_rank",
            "normalized_title",
            "pk",
        )

    @staticmethod
    def _rank_expression() -> Case:
        """Return the public integer tier annotation."""

        return Case(
            When(
                _search_identifier_hit=True,
                then=Value(MatchTier.EXACT_IDENTIFIER.value),
            ),
            When(_search_phrase_hit=True, then=Value(MatchTier.EXACT_PHRASE.value)),
            When(_search_keyword_hit=True, then=Value(MatchTier.KEYWORD.value)),
            default=Value(MatchTier.BROAD_LEXICAL.value),
            output_field=IntegerField(),
        )

    @staticmethod
    def _explanation_expression() -> Case:
        """Return explanation text kept in lockstep with ranking tiers."""

        return Case(
            When(
                _search_identifier_hit=True,
                then=Value(MatchExplanation.EXACT_IDENTIFIER.value),
            ),
            When(_search_phrase_hit=True, then=Value(MatchExplanation.EXACT_PHRASE.value)),
            When(_search_keyword_hit=True, then=Value(MatchExplanation.KEYWORD.value)),
            default=Value(MatchExplanation.BROAD_LEXICAL.value),
            output_field=TextField(),
        )
