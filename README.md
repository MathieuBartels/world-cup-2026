# world-cup-2026

Polymarket odds and Monte Carlo simulation for a World Cup 2026 office pool (poule).

## Setup

```bash
pip install -e .
```

## Usage

Fetch the highest-probability exact score for every group-stage match:

```bash
wc26 exact-scores
```

Write results to JSON and update project trackers:

```bash
wc26 exact-scores --json
```

## Output

- Terminal report grouped by group (A–L)
- JSON cache: `data/odds/exact_scores_latest.json`
- Tracker updates: `docs/trackers/state.yaml`, `log.md`

## Documentation

- [Project plan](docs/PLAN.md)
- [Trackers](docs/trackers/) — state, phases, log, learnings

## Data

- Fixtures: `data/fixtures/group_stage.yaml` (72 group-stage matches)
- Team aliases: `data/team_aliases.yaml` (FIFA names → Polymarket codes)

## Polymarket

Odds are fetched from the public [Gamma API](https://gamma-api.polymarket.com). Exact-score markets use slug pattern:

```
fifwc-{home}-{away}-{date}-exact-score
```

Example: [Mexico vs South Africa](https://polymarket.com/sports/world-cup/fifwc-mex-rsa-2026-06-11)
