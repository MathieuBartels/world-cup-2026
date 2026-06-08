# Learnings and Decisions

Architectural decisions, API gotchas, and things we learned the hard way.

---

## Polymarket API

### Exact-score is a sibling event

The main match event (`fifwc-mex-rsa-2026-06-11`) only contains moneyline markets. Exact-score markets live in a **separate event** with slug suffix `-exact-score`.

### Slug pattern is reliable

Once you know home/away abbreviations and date:

```
fifwc-{home_abbr}-{away_abbr}-{YYYY-MM-DD}-exact-score
```

### "Any Other Score" catch-all

Every exact-score event includes `Exact Score: Any Other Score?`. Exclude this when ranking highest **named** scoreline; report it separately if useful.

### Binary markets over-sum

Each scoreline is an independent Yes/No market. Probabilities across all scorelines typically sum to **more than 100%**. Normalization is required before Monte Carlo sampling.

### API access

Bare `urllib` requests may return **403 Forbidden**. Use `httpx` with a browser-like `User-Agent` header.

### Resolution window

Markets resolve on **90 minutes + stoppage time**. Extra time and penalties do not count for group-stage match markets.

---

## Team abbreviations

Polymarket uses 3-letter codes (`mex`, `rsa`, `nld`). FIFA official names differ (Korea Republic, Côte d'Ivoire, Cabo Verde, Congo DR, Türkiye). Maintain `data/team_aliases.yaml` and optionally refresh from `GET /teams?league=fifwc`.

---

## Polymarket slug date vs FIFA date

Polymarket slug dates can differ from the official FIFA kickoff date by one day when late-night ET games roll into the next UTC calendar day. Use Polymarket's slug date in `polymarket_slug`, not the FIFA schedule date.

Examples:
- Australia vs Türkiye: FIFA `2026-06-13` → Polymarket `fifwc-aus-tur-2026-06-14`
- Austria vs Jordan: FIFA `2026-06-16` → Polymarket `fifwc-aut-jor-2026-06-17`
- Tunisia vs Japan: FIFA `2026-06-20` → Polymarket `fifwc-tun-jpn-2026-06-21`

## Coverage

Not all 72 group-stage matches may have exact-score markets at any given time. Polymarket rolls them out gradually. Always track `found` vs `missing` counts in `state.yaml`.

---

## Poule context

User wants exact **match scores** (not full group standing permutations) for the poule. Monte Carlo and poule scoring rules are Phase 2.
