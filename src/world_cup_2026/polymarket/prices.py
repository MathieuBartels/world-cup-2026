from __future__ import annotations

from typing import Any

from world_cup_2026.polymarket.client import parse_json_field


def yes_probability_from_prices(yes_price: float, no_price: float) -> float:
    """Implied Yes probability using both binary legs (lowest decimal odd wins)."""
    candidates: list[float] = []
    if 0 < yes_price < 1:
        candidates.append(yes_price)
    if 0 < no_price < 1:
        candidates.append(1.0 - no_price)
    if not candidates:
        return 0.0
    return max(candidates)


def market_probability(market: dict[str, Any]) -> float:
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

    prob = yes_probability_from_prices(yes_price, no_price)

    best_bid = market.get("bestBid")
    if best_bid is not None:
        try:
            bid = float(best_bid)
            if bid > prob:
                return bid
        except (TypeError, ValueError):
            pass
    return prob
