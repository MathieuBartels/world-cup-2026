from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from world_cup_2026.fixtures import load_fixtures
from world_cup_2026.models import ExactScoresReport, MatchExactScoreResult
from world_cup_2026.polymarket.client import PolymarketClient
from world_cup_2026.polymarket.exact_score import fetch_exact_scores_for_fixture
from world_cup_2026.trackers import append_log, mark_phases_complete, update_state

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = _PACKAGE_ROOT / "data" / "odds" / "exact_scores_latest.json"

console = Console()


def fetch_all_exact_scores(fixtures_path: Path | None = None) -> list[MatchExactScoreResult]:
    fixtures = load_fixtures(fixtures_path)
    results: list[MatchExactScoreResult] = []

    with PolymarketClient() as client:
        for i, fixture in enumerate(fixtures, 1):
            console.print(f"[dim][{i}/{len(fixtures)}][/dim] {fixture.home} vs {fixture.away}...", end="\r")
            results.append(fetch_exact_scores_for_fixture(client, fixture))

    console.print(" " * 60)
    return results


def build_report(results: list[MatchExactScoreResult]) -> ExactScoresReport:
    found = sum(1 for r in results if r.found)
    return ExactScoresReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        total=len(results),
        found=found,
        missing=len(results) - found,
        results=results,
    )


def print_report(report: ExactScoresReport) -> None:
    grouped: dict[str, list[MatchExactScoreResult]] = {}
    for result in report.results:
        grouped.setdefault(result.fixture.group, []).append(result)

    for group in sorted(grouped):
        console.rule(f"[bold]Group {group}[/bold]")
        for result in sorted(grouped[group], key=lambda r: (r.fixture.date, r.fixture.match_number)):
            fixture = result.fixture
            header = f"{fixture.home} vs {fixture.away} ({fixture.date})"
            if result.found and result.top_score:
                top = result.top_score
                pct = top.probability * 100
                odds = top.decimal_odds
                odds_str = f"{odds:.2f}" if odds else "—"
                console.print(f"  [green]{header}[/green]")
                console.print(f"    Top exact score: [bold]{top.label}[/bold]  ({pct:.1f}% · {odds_str} decimal)")
                console.print(f"    [link={fixture.polymarket_url}]{fixture.polymarket_url}[/link]")
            else:
                console.print(f"  [yellow]{header}[/yellow]")
                console.print(f"    [red][MISSING][/red] {result.error or 'exact-score market not found'}")

    table = Table(title="Coverage Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Total matches", str(report.total))
    table.add_row("Found", str(report.found))
    table.add_row("Missing", str(report.missing))
    table.add_row("Coverage", f"{report.found / report.total * 100:.1f}%")
    console.print()
    console.print(table)


def write_json_report(report: ExactScoresReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump(mode="json")
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def cmd_exact_scores(args: argparse.Namespace) -> int:
    results = fetch_all_exact_scores(args.fixtures)
    report = build_report(results)

    print_report(report)

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT
    if args.json or args.output:
        write_json_report(report, output_path)
        console.print(f"\n[dim]Wrote {output_path}[/dim]")

    update_state(
        found=report.found,
        missing=report.missing,
        total=report.total,
        last_output=str(output_path) if (args.json or args.output) else "stdout only",
    )
    mark_phases_complete(["scaffold", "fixtures", "polymarket", "exact_scores"])
    append_log(
        title="Exact-score fetch run",
        phase="exact_scores",
        what=f"Fetched exact-score odds for {report.total} group-stage matches.",
        result=f"Found {report.found}/{report.total} ({report.found / report.total * 100:.1f}% coverage).",
        next_step="Re-run as Polymarket adds markets; begin Monte Carlo phase when coverage is sufficient.",
    )

    return 0 if report.missing == 0 else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wc26", description="World Cup 2026 poule tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    exact_parser = subparsers.add_parser(
        "exact-scores",
        help="Fetch highest-probability exact score per group-stage match",
    )
    exact_parser.add_argument(
        "--json",
        action="store_true",
        help="Write JSON report to data/odds/exact_scores_latest.json",
    )
    exact_parser.add_argument(
        "--output",
        "-o",
        help="Custom JSON output path",
    )
    exact_parser.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="Path to group_stage.yaml (default: data/fixtures/group_stage.yaml)",
    )
    exact_parser.set_defaults(func=cmd_exact_scores)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
