"""Tests for scenario transformation and replicated simulation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wearable_twin.simulation import (
    analytic_expectations,
    apply_promotion_intervention,
    generate_common_random_numbers,
    simulate_scenario,
)


BASELINE = np.array(
    [
        [0.5, 0.4, 0.1],
        [0.2, 0.6, 0.2],
        [0.1, 0.2, 0.7],
    ]
)


class SimulationTests(unittest.TestCase):
    def test_zero_promotion_leaves_matrix_unchanged(self) -> None:
        self.assertTrue(np.allclose(apply_promotion_intervention(BASELINE, 0), BASELINE))

    def test_promotion_preserves_rows_and_increases_high_probability(self) -> None:
        promoted = apply_promotion_intervention(BASELINE, 0.10)

        self.assertTrue(np.allclose(promoted.sum(axis=1), 1))
        self.assertTrue(np.all(promoted[:, 2] >= BASELINE[:, 2]))

    def test_simulation_is_reproducible_with_shared_inputs(self) -> None:
        random_numbers = generate_common_random_numbers(20, 10, seed=6644)
        step_pools = {
            "Low": np.array([1000, 2000]),
            "Moderate": np.array([6000, 8000]),
            "High": np.array([11000, 14000]),
        }
        initial = np.array([0.3, 0.4, 0.3])

        first = simulate_scenario(
            "Baseline", BASELINE, initial, step_pools, random_numbers
        )
        second = simulate_scenario(
            "Baseline", BASELINE, initial, step_pools, random_numbers
        )

        self.assertTrue(first.equals(second))

    def test_analytic_expectation_for_identity_chain(self) -> None:
        identity = np.eye(3)
        initial = np.array([0.2, 0.3, 0.5])
        step_means = np.array([2000.0, 7000.0, 12000.0])

        expected = analytic_expectations(identity, initial, step_means, days=30)

        self.assertAlmostEqual(expected["LowDayProportion"], 0.2)
        self.assertAlmostEqual(expected["HighDayProportion"], 0.5)
        self.assertAlmostEqual(expected["EndingHigh"], 0.5)
        self.assertAlmostEqual(expected["MeanDailySteps"], 8500.0)


if __name__ == "__main__":
    unittest.main()
