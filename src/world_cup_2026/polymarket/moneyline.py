from __future__ import annotations

from typing import Any, Literal

from world_cup_2026.models import LikelyWinnerOutcome, MatchFixture, MoneylineOdds
from world_cup_2026.polymarket.client import PolymarketClient
from world_cup_2026.polymarket.prices import market_probability

WinnerSide = Literal["home", "away", "draw"]


def _classify_moneyline_side(group_item_title: str, fixture: MatchFixture) -> WinnerSide | None:
    if group_item_title.startswith("Draw"):
        return "draw"
    if group_item_title == fixture.home:
        return "home"
    if group_item_title == fixture.away:
        return "away"
    if fixture.home in group_item_title:
        return "home"
    if fixture.away in group_item_title:
        return "away"
    return None


def _winner_label(side: WinnerSide, fixture: MatchFixture) -> str:
    if side == "home":
        return fixture.home
    if side == "away":
        return fixture.away
    return "Draw"


def parse_moneyline_event(
    event: dict[str, Any],
    fixture: MatchFixture,
) -> list[LikelyWinnerOutcome]:
    outcomes: list[LikelyWinnerOutcome] = []
    for market in event.get("markets") or []:
        title = market.get("groupItemTitle") or ""
        side = _classify_moneyline_side(title, fixture)
        if side is None:
            continue
        outcomes.append(
            LikelyWinnerOutcome(
                label=_winner_label(side, fixture),
                side=side,
                probability=market_probability(market),
            )
        )
    return outcomes


def build_moneyline_odds(outcomes: list[LikelyWinnerOutcome]) -> MoneylineOdds | None:
    by_side = {o.side: o for o in outcomes}
    if not {"home", "away", "draw"}.issubset(by_side):
        return None
    return MoneylineOdds(home=by_side["home"], away=by_side["away"], draw=by_side["draw"])


def fetch_moneyline(
    client: PolymarketClient,
    fixture: MatchFixture,
) -> MoneylineOdds | None:
    try:
        event = client.get_event_by_slug(fixture.polymarket_slug)
    except Exception:  # noqa: BLE001
        return None
    if event is None:
        return None
    outcomes = parse_moneyline_event(event, fixture)
    return build_moneyline_odds(outcomes)
