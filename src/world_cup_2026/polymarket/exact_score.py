from __future__ import annotations

import re
from typing import Any

from world_cup_2026.models import ExactScoreOutcome, MatchExactScoreResult, MatchFixture
from world_cup_2026.polymarket.client import PolymarketClient
from world_cup_2026.polymarket.moneyline import fetch_moneyline
from world_cup_2026.polymarket.prices import market_probability

# "Exact Score: Mexico 1 - 0 South Africa?" or "Exact Score: Mexico 2 – 1 South Africa?"
_SCORE_PATTERN = re.compile(
    r"Exact Score:\s*.+?\s+(\d+)\s*[-–]\s*(\d+)\s*.+?\?",
    re.IGNORECASE,
)
_OTHER_PATTERN = re.compile(r"Any Other Score", re.IGNORECASE)


def parse_exact_score_market(market: dict[str, Any]) -> ExactScoreOutcome | None:
    question = market.get("question") or ""
    probability = market_probability(market)

    if _OTHER_PATTERN.search(question):
        return ExactScoreOutcome(
            label="Any Other Score",
            probability=probability,
            is_other=True,
        )

    match = _SCORE_PATTERN.search(question)
    if not match:
        return None

    home_goals, away_goals = int(match.group(1)), int(match.group(2))
    return ExactScoreOutcome(
        home_goals=home_goals,
        away_goals=away_goals,
        label=f"{home_goals}-{away_goals}",
        probability=probability,
        is_other=False,
    )


def parse_exact_score_event(event: dict[str, Any]) -> list[ExactScoreOutcome]:
    outcomes: list[ExactScoreOutcome] = []
    for market in event.get("markets") or []:
        parsed = parse_exact_score_market(market)
        if parsed is not None:
            outcomes.append(parsed)
    return outcomes


def pick_top_score(outcomes: list[ExactScoreOutcome]) -> tuple[ExactScoreOutcome | None, ExactScoreOutcome | None]:
    named = [o for o in outcomes if not o.is_other]
    other = next((o for o in outcomes if o.is_other), None)
    if not named:
        return other, other
    top_named = max(named, key=lambda o: o.probability)
    if other is not None and other.probability > top_named.probability:
        return other, other
    return top_named, other


def fetch_exact_scores_for_fixture(
    client: PolymarketClient,
    fixture: MatchFixture,
) -> MatchExactScoreResult:
    moneyline = fetch_moneyline(client, fixture)

    try:
        event = client.get_event_by_slug(fixture.exact_score_slug)
    except Exception as exc:  # noqa: BLE001
        return MatchExactScoreResult(
            fixture=fixture,
            found=False,
            moneyline=moneyline,
            error=str(exc),
        )

    if event is None:
        return MatchExactScoreResult(
            fixture=fixture,
            found=False,
            moneyline=moneyline,
            error="exact-score event not found",
        )

    outcomes = parse_exact_score_event(event)
    if not outcomes:
        return MatchExactScoreResult(
            fixture=fixture,
            found=False,
            moneyline=moneyline,
            error="no exact-score markets in event",
        )

    top, other = pick_top_score(outcomes)
    return MatchExactScoreResult(
        fixture=fixture,
        found=top is not None,
        top_score=top,
        other_score=other,
        moneyline=moneyline,
        all_outcomes=sorted(outcomes, key=lambda o: o.probability, reverse=True),
    )
