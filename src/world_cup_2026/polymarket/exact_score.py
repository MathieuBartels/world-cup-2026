from __future__ import annotations

import re
from typing import Any

from world_cup_2026.models import ExactScoreOutcome, MatchExactScoreResult, MatchFixture
from world_cup_2026.polymarket.client import PolymarketClient, parse_json_field

# "Exact Score: Mexico 1 - 0 South Africa?" or "Exact Score: Mexico 2 – 1 South Africa?"
_SCORE_PATTERN = re.compile(
    r"Exact Score:\s*.+?\s+(\d+)\s*[-–]\s*(\d+)\s*.+?\?",
    re.IGNORECASE,
)
_OTHER_PATTERN = re.compile(r"Any Other Score", re.IGNORECASE)


def _yes_probability_from_prices(yes_price: float, no_price: float) -> float:
    """Implied Yes probability using both binary legs (lowest decimal odd wins)."""
    candidates: list[float] = []
    if 0 < yes_price < 1:
        candidates.append(yes_price)
    if 0 < no_price < 1:
        candidates.append(1.0 - no_price)
    if not candidates:
        return 0.0
    # Lowest decimal odd for Yes = highest implied probability across quotes.
    return max(candidates)


def _market_probability(market: dict[str, Any]) -> float:
    prices = parse_json_field(market.get("outcomePrices") or "[]")
    if not prices:
        return 0.0

    try:
        yes_price = float(prices[0])
    except (TypeError, ValueError):
        yes_price = 0.0

    no_price = 0.0
    if len(prices) >= 2:
        try:
            no_price = float(prices[1])
        except (TypeError, ValueError):
            pass

    prob = _yes_probability_from_prices(yes_price, no_price)

    # Prefer live order book when outcomePrices look stale
    best_bid = market.get("bestBid")
    if best_bid is not None:
        try:
            bid = float(best_bid)
            if bid > prob:
                return bid
        except (TypeError, ValueError):
            pass
    return prob


def parse_exact_score_market(market: dict[str, Any]) -> ExactScoreOutcome | None:
    question = market.get("question") or ""
    probability = _market_probability(market)

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
        return None, other
    top = max(named, key=lambda o: o.probability)
    return top, other


def fetch_exact_scores_for_fixture(
    client: PolymarketClient,
    fixture: MatchFixture,
) -> MatchExactScoreResult:
    try:
        event = client.get_event_by_slug(fixture.exact_score_slug)
    except Exception as exc:  # noqa: BLE001
        return MatchExactScoreResult(
            fixture=fixture,
            found=False,
            error=str(exc),
        )

    if event is None:
        return MatchExactScoreResult(
            fixture=fixture,
            found=False,
            error="exact-score event not found",
        )

    outcomes = parse_exact_score_event(event)
    if not outcomes:
        return MatchExactScoreResult(
            fixture=fixture,
            found=False,
            error="no exact-score markets in event",
        )

    top, other = pick_top_score(outcomes)
    return MatchExactScoreResult(
        fixture=fixture,
        found=top is not None,
        top_score=top,
        other_score=other,
        all_outcomes=sorted(outcomes, key=lambda o: o.probability, reverse=True),
    )
