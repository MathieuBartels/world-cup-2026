from __future__ import annotations

from world_cup_2026.models import MatchFixture


def build_exact_score_slug(fixture: MatchFixture) -> str:
    return fixture.exact_score_slug


def build_polymarket_url(fixture: MatchFixture) -> str:
    return fixture.polymarket_url
