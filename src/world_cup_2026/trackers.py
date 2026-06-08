from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = _PACKAGE_ROOT / "docs" / "trackers" / "state.yaml"
PHASES_PATH = _PACKAGE_ROOT / "docs" / "trackers" / "phases.yaml"
LOG_PATH = _PACKAGE_ROOT / "docs" / "trackers" / "log.md"


def update_state(
    *,
    found: int,
    missing: int,
    total: int,
    last_output: str,
) -> None:
    with STATE_PATH.open(encoding="utf-8") as f:
        state = yaml.safe_load(f) or {}

    state["current_phase"] = "exact_scores"
    state["status"] = "done" if missing == 0 else "in_progress"
    state["metrics"] = {
        "fixtures_total": total,
        "fixtures_mapped": total,
        "exact_score_events_found": found,
        "exact_score_events_missing": missing,
    }
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_output"] = last_output

    with STATE_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def mark_phases_complete(phase_ids: list[str]) -> None:
    with PHASES_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    now = datetime.now(timezone.utc).isoformat()
    for phase in data.get("phases", []):
        if phase["id"] in phase_ids:
            if phase.get("status") != "done":
                if not phase.get("started_at"):
                    phase["started_at"] = now
                phase["status"] = "done"
                phase["completed_at"] = now

    with PHASES_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def append_log(title: str, phase: str, what: str, result: str, next_step: str) -> None:
    entry = f"""## {datetime.now(timezone.utc).strftime('%Y-%m-%d')} — {title}

**Phase:** {phase}

**What:** {what}

**Result:** {result}

**Next:** {next_step}

---

"""
    existing = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else "# Work Log\n\n"
    # Insert after header
    parts = existing.split("---\n", 1)
    if len(parts) == 2:
        header = parts[0].rstrip() + "\n\n---\n\n"
        rest = parts[1]
    else:
        header = existing.rstrip() + "\n\n---\n\n"
        rest = ""
    LOG_PATH.write_text(header + entry + rest, encoding="utf-8")
