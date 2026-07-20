"""Replicated digital-twin simulation and paired scenario analysis."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import NormalDist

import numpy as np
import pandas as pd

from wearable_twin.model import STATE_ORDER


METRICS = [
    "MeanDailySteps",
    "LowDayProportion",
    "HighDayProportion",
    "EndingHigh",
]


@dataclass(frozen=True)
class CommonRandomNumbers:
    """Random inputs reused across every scenario."""

    initial: np.ndarray
    transitions: np.ndarray
    steps: np.ndarray


def validate_transition_matrix(matrix: np.ndarray) -> np.ndarray:
    """Validate and return a numeric 3-by-3 transition matrix."""
    array = np.asarray(matrix, dtype=float)
    expected_shape = (len(STATE_ORDER), len(STATE_ORDER))
    if array.shape != expected_shape:
        raise ValueError(f"Transition matrix must have shape {expected_shape}")
    if not np.isfinite(array).all() or (array < 0).any():
        raise ValueError("Transition probabilities must be finite and nonnegative")
    if not np.allclose(array.sum(axis=1), 1.0):
        raise ValueError("Every transition-matrix row must sum to one")
    return array


def apply_promotion_intervention(
    baseline_matrix: np.ndarray, promotion_probability: float
) -> np.ndarray:
    """Promote a baseline next-state outcome by one level with probability q.

    Low outcomes may become Moderate, Moderate outcomes may become High, and
    High outcomes remain High. The probability is a hypothetical sensitivity
    parameter, not an estimated treatment effect.
    """
    baseline = validate_transition_matrix(baseline_matrix)
    if not 0 <= promotion_probability <= 1:
        raise ValueError("Promotion probability must lie between zero and one")

    q = promotion_probability
    promotion_kernel = np.array(
        [
            [1 - q, q, 0.0],
            [0.0, 1 - q, q],
            [0.0, 0.0, 1.0],
        ]
    )
    return validate_transition_matrix(baseline @ promotion_kernel)


def generate_common_random_numbers(
    replications: int, days: int, seed: int
) -> CommonRandomNumbers:
    """Generate independent streams that are shared across scenarios."""
    if replications < 2:
        raise ValueError("At least two replications are required")
    if days < 2:
        raise ValueError("Simulation horizon must be at least two days")
    rng = np.random.default_rng(seed)
    return CommonRandomNumbers(
        initial=rng.random(replications),
        transitions=rng.random((replications, days - 1)),
        steps=rng.random((replications, days)),
    )


def _draw_categorical(probabilities: np.ndarray, uniforms: np.ndarray) -> np.ndarray:
    cumulative = np.cumsum(probabilities)
    return np.searchsorted(cumulative, uniforms, side="right").clip(
        max=len(probabilities) - 1
    )


def simulate_scenario(
    scenario_name: str,
    matrix: np.ndarray,
    initial_distribution: np.ndarray,
    step_pools: dict[str, np.ndarray],
    random_numbers: CommonRandomNumbers,
) -> pd.DataFrame:
    """Simulate one scenario and return one metrics row per replication."""
    transition_matrix = validate_transition_matrix(matrix)
    initial = np.asarray(initial_distribution, dtype=float)
    if initial.shape != (len(STATE_ORDER),) or (initial < 0).any():
        raise ValueError("Initial distribution must contain one nonnegative value per state")
    if not np.isclose(initial.sum(), 1.0):
        raise ValueError("Initial distribution must sum to one")
    for state in STATE_ORDER:
        if state not in step_pools or len(step_pools[state]) == 0:
            raise ValueError(f"Step pool for {state} is empty or missing")

    replications = len(random_numbers.initial)
    days = random_numbers.steps.shape[1]
    if random_numbers.transitions.shape != (replications, days - 1):
        raise ValueError("Common-random-number array shapes are inconsistent")

    states = np.empty((replications, days), dtype=np.int8)
    states[:, 0] = _draw_categorical(initial, random_numbers.initial)
    for day in range(1, days):
        uniforms = random_numbers.transitions[:, day - 1]
        for from_index in range(len(STATE_ORDER)):
            mask = states[:, day - 1] == from_index
            states[mask, day] = _draw_categorical(
                transition_matrix[from_index], uniforms[mask]
            )

    simulated_steps = np.empty((replications, days), dtype=float)
    for state_index, state in enumerate(STATE_ORDER):
        pool = np.sort(np.asarray(step_pools[state], dtype=float))
        mask = states == state_index
        pool_indices = np.minimum(
            (random_numbers.steps[mask] * len(pool)).astype(int), len(pool) - 1
        )
        simulated_steps[mask] = pool[pool_indices]

    return pd.DataFrame(
        {
            "Scenario": scenario_name,
            "Replication": np.arange(1, replications + 1),
            "MeanDailySteps": simulated_steps.mean(axis=1),
            "LowDayProportion": np.mean(states == 0, axis=1),
            "HighDayProportion": np.mean(states == 2, axis=1),
            "EndingHigh": (states[:, -1] == 2).astype(float),
        }
    )


def analytic_expectations(
    matrix: np.ndarray,
    initial_distribution: np.ndarray,
    state_step_means: np.ndarray,
    days: int,
) -> dict[str, float]:
    """Calculate exact finite-horizon expectations for validation."""
    transition_matrix = validate_transition_matrix(matrix)
    distribution = np.asarray(initial_distribution, dtype=float)
    step_means = np.asarray(state_step_means, dtype=float)
    if distribution.shape != (len(STATE_ORDER),) or not np.isclose(distribution.sum(), 1):
        raise ValueError("Initial distribution must contain three probabilities summing to one")
    if step_means.shape != (len(STATE_ORDER),):
        raise ValueError("State step means must contain one value per state")
    if days < 1:
        raise ValueError("Days must be positive")

    distributions = []
    for _ in range(days):
        distributions.append(distribution.copy())
        distribution = distribution @ transition_matrix
    daily_distributions = np.asarray(distributions)
    return {
        "MeanDailySteps": float(np.mean(daily_distributions @ step_means)),
        "LowDayProportion": float(daily_distributions[:, 0].mean()),
        "HighDayProportion": float(daily_distributions[:, 2].mean()),
        "EndingHigh": float(daily_distributions[-1, 2]),
    }


def _mean_interval(values: pd.Series, confidence_level: float) -> tuple[float, float, float, float]:
    count = len(values)
    mean = float(values.mean())
    standard_error = float(values.std(ddof=1) / np.sqrt(count))
    critical_value = NormalDist().inv_cdf(0.5 + confidence_level / 2)
    half_width = critical_value * standard_error
    return mean, standard_error, mean - half_width, mean + half_width


def summarize_scenarios(
    results: pd.DataFrame, confidence_level: float
) -> pd.DataFrame:
    """Summarize each scenario metric with a normal-theory confidence interval."""
    rows = []
    for scenario, group in results.groupby("Scenario", sort=False):
        for metric in METRICS:
            mean, standard_error, lower, upper = _mean_interval(
                group[metric], confidence_level
            )
            rows.append(
                {
                    "Scenario": scenario,
                    "Metric": metric,
                    "Replications": len(group),
                    "Mean": mean,
                    "StandardError": standard_error,
                    "Lower": lower,
                    "Upper": upper,
                }
            )
    return pd.DataFrame(rows)


def paired_comparisons(
    results: pd.DataFrame,
    confidence_level: float,
    baseline_name: str = "Baseline",
) -> pd.DataFrame:
    """Compare interventions with baseline using replication-matched differences."""
    baseline = results.loc[results["Scenario"].eq(baseline_name)].set_index("Replication")
    if baseline.empty:
        raise ValueError(f"Baseline scenario {baseline_name!r} was not found")

    rows = []
    for scenario in results["Scenario"].drop_duplicates():
        if scenario == baseline_name:
            continue
        candidate = results.loc[results["Scenario"].eq(scenario)].set_index("Replication")
        if not candidate.index.equals(baseline.index):
            raise ValueError("Scenario replications do not align with baseline")
        for metric in METRICS:
            differences = candidate[metric] - baseline[metric]
            mean, standard_error, lower, upper = _mean_interval(
                differences, confidence_level
            )
            rows.append(
                {
                    "Scenario": scenario,
                    "Baseline": baseline_name,
                    "Metric": metric,
                    "Replications": len(differences),
                    "MeanDifference": mean,
                    "StandardError": standard_error,
                    "Lower": lower,
                    "Upper": upper,
                    "IntervalExcludesZero": bool(lower > 0 or upper < 0),
                }
            )
    return pd.DataFrame(rows)
