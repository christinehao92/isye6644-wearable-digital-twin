"""Activity-state construction and Markov transition-model estimation."""

from __future__ import annotations

from statistics import NormalDist
from typing import Any

import numpy as np
import pandas as pd


STATE_ORDER = ["Low", "Moderate", "High"]


def assign_activity_states(
    daily: pd.DataFrame,
    low_upper_exclusive: int = 5000,
    moderate_upper_exclusive: int = 10000,
    exclude_zero_step_days: bool = True,
) -> pd.DataFrame:
    """Assign interpretable daily step-count states."""
    if low_upper_exclusive <= 0:
        raise ValueError("The low-state upper threshold must be positive")
    if moderate_upper_exclusive <= low_upper_exclusive:
        raise ValueError("The moderate threshold must exceed the low threshold")
    if "TotalSteps" not in daily or "ActivityDate" not in daily or "Id" not in daily:
        raise ValueError("Daily data must include Id, ActivityDate, and TotalSteps")

    stated = daily.copy()
    if exclude_zero_step_days:
        stated = stated.loc[stated["TotalSteps"].gt(0)].copy()

    stated["ActivityState"] = pd.cut(
        stated["TotalSteps"],
        bins=[0, low_upper_exclusive, moderate_upper_exclusive, np.inf],
        labels=STATE_ORDER,
        right=False,
        ordered=True,
    )
    if stated["ActivityState"].isna().any():
        raise ValueError("Some retained days could not be assigned an activity state")
    return stated.sort_values(["Id", "ActivityDate"]).reset_index(drop=True)


def build_transition_records(stated: pd.DataFrame) -> pd.DataFrame:
    """Return transitions only when two observations are one calendar day apart."""
    ordered = stated.sort_values(["Id", "ActivityDate"]).copy()
    ordered["NextDate"] = ordered.groupby("Id")["ActivityDate"].shift(-1)
    ordered["NextState"] = ordered.groupby("Id", observed=True)["ActivityState"].shift(-1)
    consecutive = ordered["NextDate"].sub(ordered["ActivityDate"]).dt.days.eq(1)

    transitions = ordered.loc[
        consecutive, ["Id", "ActivityDate", "ActivityState", "NextState"]
    ].rename(
        columns={
            "ActivityDate": "FromDate",
            "ActivityState": "FromState",
            "NextState": "ToState",
        }
    )
    transitions["FromState"] = pd.Categorical(
        transitions["FromState"], categories=STATE_ORDER, ordered=True
    )
    transitions["ToState"] = pd.Categorical(
        transitions["ToState"], categories=STATE_ORDER, ordered=True
    )
    return transitions.reset_index(drop=True)


def transition_counts(transitions: pd.DataFrame) -> pd.DataFrame:
    """Count every from-state/to-state combination."""
    return pd.crosstab(
        transitions["FromState"],
        transitions["ToState"],
        dropna=False,
    ).reindex(index=STATE_ORDER, columns=STATE_ORDER, fill_value=0)


def normalize_transition_counts(
    counts: pd.DataFrame, pseudocount: float = 0.0
) -> pd.DataFrame:
    """Convert transition counts to row probabilities."""
    if pseudocount < 0:
        raise ValueError("Pseudocount cannot be negative")
    adjusted = counts.astype(float) + pseudocount
    row_totals = adjusted.sum(axis=1)
    if row_totals.eq(0).any():
        empty_states = row_totals.index[row_totals.eq(0)].tolist()
        raise ValueError(f"Cannot normalize states with no transitions: {empty_states}")
    return adjusted.div(row_totals, axis=0)


def bootstrap_transition_intervals(
    transitions: pd.DataFrame,
    replications: int,
    confidence_level: float,
    seed: int,
) -> pd.DataFrame:
    """Cluster-bootstrap participants to quantify transition uncertainty."""
    if replications < 2:
        raise ValueError("At least two bootstrap replications are required")
    if not 0 < confidence_level < 1:
        raise ValueError("Confidence level must lie between zero and one")

    participant_counts = {
        participant: transition_counts(group).to_numpy(dtype=float)
        for participant, group in transitions.groupby("Id", sort=True, observed=True)
    }
    participants = np.asarray(list(participant_counts))
    if len(participants) < 2:
        raise ValueError("At least two participants are required for cluster bootstrap")

    rng = np.random.default_rng(seed)
    estimates = np.empty((replications, len(STATE_ORDER), len(STATE_ORDER)))
    for replication in range(replications):
        sampled = rng.choice(participants, size=len(participants), replace=True)
        counts = sum(participant_counts[participant] for participant in sampled)
        row_totals = counts.sum(axis=1, keepdims=True)
        estimates[replication] = np.divide(
            counts,
            row_totals,
            out=np.full_like(counts, np.nan),
            where=row_totals > 0,
        )

    alpha = 1 - confidence_level
    lower = np.nanquantile(estimates, alpha / 2, axis=0)
    upper = np.nanquantile(estimates, 1 - alpha / 2, axis=0)
    point = normalize_transition_counts(transition_counts(transitions)).to_numpy()

    rows = []
    for from_index, from_state in enumerate(STATE_ORDER):
        for to_index, to_state in enumerate(STATE_ORDER):
            rows.append(
                {
                    "FromState": from_state,
                    "ToState": to_state,
                    "Estimate": point[from_index, to_index],
                    "Lower": lower[from_index, to_index],
                    "Upper": upper[from_index, to_index],
                }
            )
    return pd.DataFrame(rows)


def chronological_validation(
    transitions: pd.DataFrame,
    training_fraction: float = 0.75,
    pseudocount: float = 0.5,
) -> dict[str, Any]:
    """Compare the transition model with a state-frequency baseline on later data."""
    if not 0.5 <= training_fraction < 1:
        raise ValueError("Training fraction must be in [0.5, 1)")

    unique_dates = np.sort(transitions["FromDate"].unique())
    cutoff_index = max(0, int(np.ceil(len(unique_dates) * training_fraction)) - 1)
    cutoff = pd.Timestamp(unique_dates[cutoff_index])
    train = transitions.loc[transitions["FromDate"].le(cutoff)]
    test = transitions.loc[transitions["FromDate"].gt(cutoff)]
    if train.empty or test.empty:
        raise ValueError("Chronological split produced an empty train or test set")

    matrix = normalize_transition_counts(transition_counts(train), pseudocount)
    destination_counts = (
        train["ToState"].value_counts(sort=False).reindex(STATE_ORDER, fill_value=0).astype(float)
        + pseudocount
    )
    baseline = destination_counts / destination_counts.sum()

    transition_probabilities = np.asarray(
        [matrix.loc[row.FromState, row.ToState] for row in test.itertuples()]
    )
    baseline_probabilities = np.asarray([baseline.loc[state] for state in test["ToState"]])
    model_predictions = matrix.idxmax(axis=1)
    predicted_states = np.asarray([model_predictions.loc[state] for state in test["FromState"]])

    model_log_loss = float(-np.log(transition_probabilities).mean())
    baseline_log_loss = float(-np.log(baseline_probabilities).mean())
    return {
        "training_fraction": training_fraction,
        "cutoff_date": cutoff.date().isoformat(),
        "training_transitions": int(len(train)),
        "test_transitions": int(len(test)),
        "transition_model_log_loss": model_log_loss,
        "state_frequency_baseline_log_loss": baseline_log_loss,
        "log_loss_improvement_vs_baseline": baseline_log_loss - model_log_loss,
        "transition_model_accuracy": float(
            np.mean(predicted_states == test["ToState"].astype(str).to_numpy())
        ),
    }
