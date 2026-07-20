"""Publication-quality figures for the wearable digital-twin report."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wearable_twin.model import STATE_ORDER


SCENARIO_ORDER = ["Baseline", "Light", "Moderate", "Strong"]
SCENARIO_COLORS = ["#4C78A8", "#72B7B2", "#F2CF5B", "#E45756"]


def configure_style() -> None:
    """Set a restrained, readable report style."""
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.25,
            "legend.frameon": False,
        }
    )


def save_transition_heatmap(matrix: pd.DataFrame, destination: Path) -> None:
    """Plot the fitted state-transition probability matrix."""
    configure_style()
    values = matrix.reindex(index=STATE_ORDER, columns=STATE_ORDER).to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    image = ax.imshow(values, vmin=0, vmax=1, cmap="Blues")
    ax.grid(False)
    ax.set_xticks(range(len(STATE_ORDER)), STATE_ORDER)
    ax.set_yticks(range(len(STATE_ORDER)), STATE_ORDER)
    ax.set_xlabel("Next-day activity state")
    ax.set_ylabel("Current activity state")
    ax.set_title("Estimated daily activity-state transitions")

    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            color = "white" if values[row, column] >= 0.5 else "#202020"
            ax.text(
                column,
                row,
                f"{values[row, column]:.1%}",
                ha="center",
                va="center",
                color=color,
                fontweight="bold" if row == column else "normal",
            )
    colorbar = fig.colorbar(image, ax=ax, shrink=0.85)
    colorbar.set_label("Transition probability")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, bbox_inches="tight")
    plt.close(fig)


def save_scenario_outcomes(summary: pd.DataFrame, destination: Path) -> None:
    """Plot scenario means with 95% confidence intervals."""
    configure_style()
    specifications = [
        ("MeanDailySteps", "Mean daily steps", "Steps per day", "{:,.0f}"),
        ("HighDayProportion", "High-activity days", "Proportion of days", "{:.1%}"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    x = np.arange(len(SCENARIO_ORDER))

    for ax, (metric, title, ylabel, formatter) in zip(axes, specifications):
        data = (
            summary.loc[summary["Metric"].eq(metric)]
            .set_index("Scenario")
            .reindex(SCENARIO_ORDER)
        )
        means = data["Mean"].to_numpy()
        lower_error = means - data["Lower"].to_numpy()
        upper_error = data["Upper"].to_numpy() - means
        bars = ax.bar(x, means, color=SCENARIO_COLORS, width=0.68)
        ax.errorbar(
            x,
            means,
            yerr=np.vstack([lower_error, upper_error]),
            fmt="none",
            ecolor="#202020",
            capsize=4,
            linewidth=1.2,
        )
        ax.set_xticks(x, SCENARIO_ORDER)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        if metric.endswith("Proportion"):
            ax.set_ylim(0, max(data["Upper"].max() * 1.22, 0.55))
        else:
            ax.set_ylim(0, data["Upper"].max() * 1.18)
        for bar, value in zip(bars, means):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                formatter.format(value),
                ha="center",
                va="bottom",
            )
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, bbox_inches="tight")
    plt.close(fig)


def save_paired_effects(comparisons: pd.DataFrame, destination: Path) -> None:
    """Plot paired intervention-minus-baseline effects and confidence intervals."""
    configure_style()
    scenario_order = ["Light", "Moderate", "Strong"]
    specifications = [
        ("MeanDailySteps", "Change in mean daily steps", "Steps per day"),
        (
            "HighDayProportion",
            "Change in high-activity days",
            "Percentage-point change",
        ),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    y = np.arange(len(scenario_order))

    for ax, (metric, title, xlabel) in zip(axes, specifications):
        data = (
            comparisons.loc[comparisons["Metric"].eq(metric)]
            .set_index("Scenario")
            .reindex(scenario_order)
        )
        means = data["MeanDifference"].to_numpy()
        lower_error = means - data["Lower"].to_numpy()
        upper_error = data["Upper"].to_numpy() - means
        scale = 100 if metric == "HighDayProportion" else 1
        ax.errorbar(
            means * scale,
            y,
            xerr=np.vstack([lower_error, upper_error]) * scale,
            fmt="o",
            color="#4C78A8",
            ecolor="#4C78A8",
            markersize=6,
            capsize=4,
            linewidth=1.5,
        )
        ax.axvline(0, color="#555555", linewidth=1)
        ax.set_yticks(y, scenario_order)
        ax.set_xlabel(xlabel)
        ax.set_title(title)
        ax.invert_yaxis()
        upper_values = data["Upper"].to_numpy() * scale
        ax.set_xlim(min(0, (data["Lower"].min() * scale) * 1.1), upper_values.max() * 1.18)
        for row_index, (value, upper_value) in enumerate(zip(means * scale, upper_values)):
            label = f"{value:,.0f}" if scale == 1 else f"{value:.1f} pp"
            ax.annotate(
                label,
                (upper_value, row_index),
                xytext=(7, 0),
                textcoords="offset points",
                va="center",
            )
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, bbox_inches="tight")
    plt.close(fig)
