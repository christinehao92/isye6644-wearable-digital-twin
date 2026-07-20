"""Tests for activity-state and transition-model construction."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wearable_twin.model import (
    assign_activity_states,
    build_transition_records,
    normalize_transition_counts,
    transition_counts,
)


class TransitionModelTests(unittest.TestCase):
    def test_state_threshold_boundaries(self) -> None:
        daily = pd.DataFrame(
            {
                "Id": ["1"] * 5,
                "ActivityDate": pd.date_range("2016-01-01", periods=5),
                "TotalSteps": [0, 4999, 5000, 9999, 10000],
            }
        )

        stated = assign_activity_states(daily)

        self.assertEqual(
            stated["ActivityState"].astype(str).tolist(),
            ["Low", "Moderate", "Moderate", "High"],
        )

    def test_only_consecutive_days_form_transitions(self) -> None:
        stated = pd.DataFrame(
            {
                "Id": ["1", "1", "1"],
                "ActivityDate": pd.to_datetime(
                    ["2016-01-01", "2016-01-02", "2016-01-04"]
                ),
                "ActivityState": pd.Categorical(
                    ["Low", "Moderate", "High"],
                    categories=["Low", "Moderate", "High"],
                    ordered=True,
                ),
            }
        )

        transitions = build_transition_records(stated)

        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions.loc[0, "FromState"], "Low")
        self.assertEqual(transitions.loc[0, "ToState"], "Moderate")

    def test_transition_probabilities_sum_to_one(self) -> None:
        transitions = pd.DataFrame(
            {
                "FromState": pd.Categorical(
                    ["Low", "Low", "Moderate", "High"],
                    categories=["Low", "Moderate", "High"],
                ),
                "ToState": pd.Categorical(
                    ["Low", "Moderate", "High", "High"],
                    categories=["Low", "Moderate", "High"],
                ),
            }
        )

        matrix = normalize_transition_counts(transition_counts(transitions))

        self.assertTrue(matrix.sum(axis=1).round(12).eq(1).all())


if __name__ == "__main__":
    unittest.main()
