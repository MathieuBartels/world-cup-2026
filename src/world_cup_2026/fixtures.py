from __future__ import annotations

from pathlib import Path

import yaml

from world_cup_2026.models import MatchFixture

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES_PATH = _PACKAGE_ROOT / "data" / "fixtures" / "group_stage.yaml"


def load_fixtures(path: Path | None = None) -> list[MatchFixture]:
    fixtures_path = path or DEFAULT_FIXTURES_PATH
    with fixtures_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [MatchFixture.model_validate(m) for m in data["matches"]]


def fixtures_by_group(fixtures: list[MatchFixture]) -> dict[str, list[MatchFixture]]:
    grouped: dict[str, list[MatchFixture]] = {}
    for fixture in fixtures:
        grouped.setdefault(fixture.group, []).append(fixture)
    for group in grouped:
        grouped[group].sort(key=lambda m: (m.date, m.match_number))
    return dict(sorted(grouped.items()))
