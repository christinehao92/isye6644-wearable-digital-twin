"""Tests for deterministic daily-activity cleaning."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wearable_twin.data import NUMERIC_COLUMNS, clean_daily_activity


def make_row(source_priority: int, steps: int) -> dict[str, object]:
    row: dict[str, object] = {
        "Id": "1",
        "ActivityDate": pd.Timestamp("2016-04-12"),
        "SourcePeriod": f"period-{source_priority}",
        "_SourcePriority": source_priority,
    }
    row.update({column: 0 for column in NUMERIC_COLUMNS})
    row["TotalSteps"] = steps
    row["LightlyActiveMinutes"] = 10
    row["SedentaryMinutes"] = 100
    return row


class CleanDailyActivityTests(unittest.TestCase):
    def test_later_source_wins_for_overlapping_person_day(self) -> None:
        raw = pd.DataFrame([make_row(0, 500), make_row(1, 8000)])

        cleaned = clean_daily_activity(raw)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.loc[0, "TotalSteps"], 8000)
        self.assertEqual(cleaned.loc[0, "RecordedMinutes"], 110)

    def test_negative_value_is_rejected(self) -> None:
        row = make_row(0, -1)

        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            clean_daily_activity(pd.DataFrame([row]))


if __name__ == "__main__":
    unittest.main()
