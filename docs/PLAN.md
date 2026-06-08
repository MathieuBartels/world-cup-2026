# World Cup 2026 Poule — Project Plan

## Objective

Build a Python tool that uses **Polymarket prediction-market odds** to support a World Cup 2026 office pool (poule):

1. **Phase 1 (current):** For every group-stage match, fetch exact-score markets and report the **highest-probability scoreline**.
2. **Phase 2 (later):** Monte Carlo simulation — sample match outcomes from Polymarket distributions, derive group standings, and suggest poule picks.

## Tournament Facts

| Item | Value |
|------|-------|
| Teams | 48 |
| Groups | 12 (A–L), 4 teams each |
| Group-stage matches | 72 |
| Dates | 11–27 June 2026 |
| Points | 3 win, 1 draw, 0 loss |
| Advancement | Top 2 per group + 8 best third-place teams → Round of 32 |

### Groups (confirmed draw, March 2026)

| Group | Teams |
|-------|-------|
| A | Mexico, South Africa, Korea Republic, Czechia |
| B | Canada, Switzerland, Qatar, Bosnia and Herzegovina |
| C | Brazil, Morocco, Haiti, Scotland |
| D | United States, Paraguay, Australia, Türkiye |
| E | Germany, Curaçao, Côte d'Ivoire, Ecuador |
| F | Netherlands, Japan, Tunisia, Sweden |
| G | Belgium, Egypt, Iran, New Zealand |
| H | Spain, Cabo Verde, Saudi Arabia, Uruguay |
| I | France, Senegal, Norway, Iraq |
| J | Argentina, Algeria, Austria, Jordan |
| K | Portugal, Uzbekistan, Colombia, Congo DR |
| L | England, Croatia, Ghana, Panama |

## Data Sources

| Source | URL / path | Purpose |
|--------|------------|---------|
| Polymarket Gamma API | `https://gamma-api.polymarket.com` | Live odds (no auth) |
| Fixtures | `data/fixtures/group_stage.yaml` | 72 match schedule |
| Team aliases | `data/team_aliases.yaml` | FIFA name → Polymarket 3-letter code |
| Cached odds | `data/odds/exact_scores_latest.json` | Latest fetch results |

## Polymarket Integration

### Event slug patterns

| Type | Pattern | Example |
|------|---------|---------|
| Moneyline | `fifwc-{home}-{away}-{date}` | `fifwc-mex-rsa-2026-06-11` |
| Exact score | `fifwc-{home}-{away}-{date}-exact-score` | `fifwc-mex-rsa-2026-06-11-exact-score` |
| Props | `fifwc-{home}-{away}-{date}-more-markets` | spreads, totals, BTTS |

### API endpoints

```
GET /events?slug={slug}
GET /public-search?q={query}
GET /teams?league=fifwc
GET /events?series_id=11433&active=true&closed=false
```

### Exact-score market format

- Question: `Exact Score: Mexico 1 - 0 South Africa?`
- Binary Yes/No; **Yes price = implied probability**
- Includes catch-all: `Exact Score: Any Other Score?`
- Resolution: **90 minutes + stoppage time** (no extra time)

### Highest-odds algorithm

1. Fetch exact-score event by slug
2. Parse all named scorelines from market questions
3. Exclude "Any Other Score"
4. Pick scoreline with highest Yes probability
5. Report probability and decimal odds (`1 / probability`)

## Monte Carlo Approach (Phase 2)

Deferred until Phase 1 coverage is acceptable.

1. **Normalize** scoreline probabilities per match (binary markets over-sum; divide by total)
2. **Sample** one scoreline per match (weighted random, fixed seed)
3. **Compute** group standings (points, GD, GF, FIFA tiebreakers)
4. **Repeat** N iterations (e.g. 10,000)
5. **Output** group outcome distributions and poule pick suggestions

Poule scoring rules to be added when provided by the user.

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Exact-score markets not live for all 72 matches | Track coverage %; retry; report missing |
| Team abbreviation mismatches | `team_aliases.yaml` + Polymarket `/teams` API |
| API 403 without User-Agent | httpx client with browser-like headers |
| Prices sum > 100% across scorelines | Normalization before Monte Carlo |
| Geographic restriction on Polymarket | API reads work; manual UI verification optional |

## Project Layout

```
docs/PLAN.md
docs/trackers/          # state, phases, log, learnings
data/fixtures/
data/odds/
src/world_cup_2026/
```

## CLI Usage

```bash
pip install -e .
wc26 exact-scores          # fetch and print report
wc26 exact-scores --json   # write data/odds/exact_scores_latest.json
```
