"""Fit and validate the daily activity-state transition model."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wearable_twin.data import clean_daily_activity, load_daily_activity
from wearable_twin.model import (
    STATE_ORDER,
    assign_activity_states,
    bootstrap_transition_intervals,
    build_transition_records,
    chronological_validation,
    normalize_transition_counts,
    transition_counts,
)


def main() -> None:
    config = json.loads((PROJECT_ROOT / "config" / "project.json").read_text())
    state_config = config["activity_state_definition"]
    if state_config["status"] != "approved":
        raise RuntimeError(
            "Activity-state definition must be marked approved in config/project.json"
        )

    daily = clean_daily_activity(load_daily_activity(PROJECT_ROOT))
    stated = assign_activity_states(
        daily,
        low_upper_exclusive=state_config["low_upper_exclusive"],
        moderate_upper_exclusive=state_config["moderate_upper_exclusive"],
        exclude_zero_step_days=state_config["exclude_zero_step_days"],
    )
    transitions = build_transition_records(stated)
    counts = transition_counts(transitions)
    matrix = normalize_transition_counts(counts)
    intervals = bootstrap_transition_intervals(
        transitions,
        replications=config["replications"],
        confidence_level=config["confidence_level"],
        seed=config["random_seed"],
    )
    validation = chronological_validation(transitions)

    outputs = PROJECT_ROOT / "outputs"
    outputs.mkdir(exist_ok=True)
    stated.to_csv(outputs / "daily_activity_states.csv", index=False)
    transitions.to_csv(outputs / "transition_records.csv", index=False)
    counts.to_csv(outputs / "transition_counts.csv")
    matrix.to_csv(outputs / "transition_matrix.csv")
    intervals.to_csv(outputs / "transition_intervals.csv", index=False)
    (outputs / "transition_validation.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )

    state_counts = stated["ActivityState"].value_counts(sort=False).reindex(STATE_ORDER)
    print("Activity-state counts")
    print(state_counts.to_string())
    print("\nTransition counts")
    print(counts.to_string())
    print("\nTransition probabilities")
    print(matrix.round(4).to_string())
    print("\nChronological validation")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
