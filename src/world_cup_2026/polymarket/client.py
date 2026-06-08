from __future__ import annotations

import json
from typing import Any

import httpx

GAMMA_API_BASE = "https://gamma-api.polymarket.com"
DEFAULT_HEADERS = {
    "User-Agent": "world-cup-2026/0.1.0 (poule odds fetcher)",
    "Accept": "application/json",
}


class PolymarketClient:
    def __init__(self, base_url: str = GAMMA_API_BASE, timeout: float = 30.0) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PolymarketClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get_event_by_slug(self, slug: str) -> dict[str, Any] | None:
        response = self._client.get("/events", params={"slug": slug})
        response.raise_for_status()
        events = response.json()
        if not events:
            return None
        return events[0]

    def get_teams(self, league: str = "fifwc", limit: int = 100) -> list[dict[str, Any]]:
        response = self._client.get("/teams", params={"league": league, "limit": limit})
        response.raise_for_status()
        return response.json()


def parse_json_field(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value
