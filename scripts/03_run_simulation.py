"""Run paired baseline and hypothetical intervention experiments."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wearable_twin.data import clean_daily_activity, load_daily_activity
from wearable_twin.model import (
    STATE_ORDER,
    assign_activity_states,
    build_transition_records,
    normalize_transition_counts,
    transition_counts,
)
from wearable_twin.simulation import (
    analytic_expectations,
    apply_promotion_intervention,
    generate_common_random_numbers,
    paired_comparisons,
    simulate_scenario,
    summarize_scenarios,
)


def main() -> None:
    config = json.loads((PROJECT_ROOT / "config" / "project.json").read_text())
    state_config = config["activity_state_definition"]
    if state_config["status"] != "approved":
        raise RuntimeError("The activity-state definition has not been approved")

    daily = clean_daily_activity(load_daily_activity(PROJECT_ROOT))
    stated = assign_activity_states(
        daily,
        low_upper_exclusive=state_config["low_upper_exclusive"],
        moderate_upper_exclusive=state_config["moderate_upper_exclusive"],
        exclude_zero_step_days=state_config["exclude_zero_step_days"],
    )
    transitions = build_transition_records(stated)
    baseline_matrix = normalize_transition_counts(transition_counts(transitions)).to_numpy()
    initial_distribution = (
        stated["ActivityState"]
        .value_counts(sort=False, normalize=True)
        .reindex(STATE_ORDER)
        .to_numpy()
    )
    step_pools = {
        state: stated.loc[stated["ActivityState"].eq(state), "TotalSteps"].to_numpy()
        for state in STATE_ORDER
    }

    random_numbers = generate_common_random_numbers(
        replications=config["replications"],
        days=config["simulation_days"],
        seed=config["random_seed"],
    )
    scenario_results = []
    scenario_matrices = []
    exact_expectations = {}
    for scenario in config["interventions"]:
        matrix = apply_promotion_intervention(
            baseline_matrix, scenario["promotion_probability"]
        )
        scenario_results.append(
            simulate_scenario(
                scenario["name"],
                matrix,
                initial_distribution,
                step_pools,
                random_numbers,
            )
        )
        exact_expectations[scenario["name"]] = analytic_expectations(
            matrix,
            initial_distribution,
            np.asarray([step_pools[state].mean() for state in STATE_ORDER]),
            config["simulation_days"],
        )
        for from_index, from_state in enumerate(STATE_ORDER):
            for to_index, to_state in enumerate(STATE_ORDER):
                scenario_matrices.append(
                    {
                        "Scenario": scenario["name"],
                        "PromotionProbability": scenario["promotion_probability"],
                        "FromState": from_state,
                        "ToState": to_state,
                        "Probability": matrix[from_index, to_index],
                    }
                )

    results = pd.concat(scenario_results, ignore_index=True)
    summary = summarize_scenarios(results, config["confidence_level"])
    comparisons = paired_comparisons(results, config["confidence_level"])
    validation_rows = []
    for row in summary.itertuples(index=False):
        exact = exact_expectations[row.Scenario][row.Metric]
        validation_rows.append(
            {
                "Scenario": row.Scenario,
                "Metric": row.Metric,
                "ExactExpectation": exact,
                "SimulationMean": row.Mean,
                "Lower": row.Lower,
                "Upper": row.Upper,
                "ExactInsideInterval": bool(row.Lower <= exact <= row.Upper),
            }
        )
    validation = pd.DataFrame(validation_rows)

    outputs = PROJECT_ROOT / "outputs"
    outputs.mkdir(exist_ok=True)
    results.to_csv(outputs / "simulation_replications.csv", index=False)
    summary.to_csv(outputs / "simulation_summary.csv", index=False)
    comparisons.to_csv(outputs / "paired_comparisons.csv", index=False)
    validation.to_csv(outputs / "simulation_validation.csv", index=False)
    pd.DataFrame(scenario_matrices).to_csv(
        outputs / "scenario_transition_matrices.csv", index=False
    )

    print("Scenario means and 95% confidence intervals")
    print(
        summary.loc[summary["Metric"].isin(["MeanDailySteps", "HighDayProportion"])]
        .round(4)
        .to_string(index=False)
    )
    print("\nPaired differences versus baseline")
    print(
        comparisons.loc[
            comparisons["Metric"].isin(["MeanDailySteps", "HighDayProportion"])
        ]
        .round(4)
        .to_string(index=False)
    )
    print("\nAnalytical validation")
    print(
        validation.groupby("Scenario", sort=False)["ExactInsideInterval"]
        .agg(["sum", "count"])
        .to_string()
    )


if __name__ == "__main__":
    main()
