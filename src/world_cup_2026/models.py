from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MatchFixture(BaseModel):
    id: str
    match_number: int
    group: str
    date: str
    home: str
    away: str
    home_abbr: str
    away_abbr: str
    polymarket_slug: str

    @property
    def exact_score_slug(self) -> str:
        return f"{self.polymarket_slug}-exact-score"

    @property
    def polymarket_url(self) -> str:
        return f"https://polymarket.com/sports/world-cup/{self.polymarket_slug}"


class ExactScoreOutcome(BaseModel):
    home_goals: int | None = None
    away_goals: int | None = None
    label: str
    probability: float
    is_other: bool = False

    @property
    def scoreline(self) -> str | None:
        if self.home_goals is None or self.away_goals is None:
            return None
        return f"{self.home_goals}-{self.away_goals}"

    @property
    def display_label(self) -> str:
        if self.is_other:
            return "Other"
        return self.label

    @property
    def decimal_odds(self) -> float | None:
        if self.probability <= 0:
            return None
        return round(1.0 / self.probability, 2)


class LikelyWinnerOutcome(BaseModel):
    label: str
    side: Literal["home", "away", "draw"]
    probability: float

    @property
    def decimal_odds(self) -> float | None:
        if self.probability <= 0:
            return None
        return round(1.0 / self.probability, 2)


class MoneylineOdds(BaseModel):
    home: LikelyWinnerOutcome
    away: LikelyWinnerOutcome
    draw: LikelyWinnerOutcome

    @property
    def likely_winner(self) -> LikelyWinnerOutcome:
        return max((self.home, self.away, self.draw), key=lambda o: o.probability)


class MatchExactScoreResult(BaseModel):
    fixture: MatchFixture
    found: bool
    top_score: ExactScoreOutcome | None = None
    other_score: ExactScoreOutcome | None = None
    moneyline: MoneylineOdds | None = None
    all_outcomes: list[ExactScoreOutcome] = Field(default_factory=list)
    error: str | None = None


class ExactScoresReport(BaseModel):
    generated_at: str
    total: int
    found: int
    missing: int
    results: list[MatchExactScoreResult]
