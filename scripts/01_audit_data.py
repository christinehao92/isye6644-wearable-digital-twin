"""Audit and clean the raw Fitbit daily activity files."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wearable_twin.data import build_audit, clean_daily_activity, load_daily_activity


def main() -> None:
    outputs = PROJECT_ROOT / "outputs"
    outputs.mkdir(exist_ok=True)

    raw = load_daily_activity(PROJECT_ROOT)
    cleaned = clean_daily_activity(raw)
    audit = build_audit(raw, cleaned)

    cleaned.to_csv(outputs / "daily_activity_clean.csv", index=False)
    (outputs / "data_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(audit, indent=2))
    print(f"\nWrote {len(cleaned):,} cleaned participant-days to outputs/.")


if __name__ == "__main__":
    main()
