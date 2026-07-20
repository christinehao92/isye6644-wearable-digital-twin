"""Generate report-ready figures and consolidated Markdown tables."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wearable_twin.plotting import (
    save_paired_effects,
    save_scenario_outcomes,
    save_transition_heatmap,
)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    separator = ["---"] + ["---:" for _ in headers[1:]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def main() -> None:
    outputs = PROJECT_ROOT / "outputs"
    figures = PROJECT_ROOT / "figures"
    required = [
        outputs / "transition_matrix.csv",
        outputs / "simulation_summary.csv",
        outputs / "paired_comparisons.csv",
    ]
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Run scripts 01 through 03 before generating assets. Missing: "
            + ", ".join(missing)
        )

    matrix = pd.read_csv(required[0], index_col=0)
    summary = pd.read_csv(required[1])
    comparisons = pd.read_csv(required[2])

    save_transition_heatmap(matrix, figures / "transition_matrix.png")
    save_scenario_outcomes(summary, figures / "scenario_outcomes.png")
    save_paired_effects(comparisons, figures / "paired_effects.png")

    scenario_order = ["Baseline", "Light", "Moderate", "Strong"]
    scenario_rows = []
    for scenario in scenario_order:
        step_row = summary.loc[
            summary["Scenario"].eq(scenario) & summary["Metric"].eq("MeanDailySteps")
        ].iloc[0]
        high_row = summary.loc[
            summary["Scenario"].eq(scenario)
            & summary["Metric"].eq("HighDayProportion")
        ].iloc[0]
        scenario_rows.append(
            [
                scenario,
                f"{step_row.Mean:,.0f} ({step_row.Lower:,.0f}, {step_row.Upper:,.0f})",
                f"{high_row.Mean:.3f} ({high_row.Lower:.3f}, {high_row.Upper:.3f})",
            ]
        )

    effect_rows = []
    for scenario in ["Light", "Moderate", "Strong"]:
        step_row = comparisons.loc[
            comparisons["Scenario"].eq(scenario)
            & comparisons["Metric"].eq("MeanDailySteps")
        ].iloc[0]
        high_row = comparisons.loc[
            comparisons["Scenario"].eq(scenario)
            & comparisons["Metric"].eq("HighDayProportion")
        ].iloc[0]
        effect_rows.append(
            [
                scenario,
                f"{step_row.MeanDifference:,.0f} ({step_row.Lower:,.0f}, {step_row.Upper:,.0f})",
                f"{100 * high_row.MeanDifference:.1f} ({100 * high_row.Lower:.1f}, {100 * high_row.Upper:.1f})",
            ]
        )

    report_tables = "\n\n".join(
        [
            "# Generated Report Tables",
            "## Scenario outcomes\n\n"
            + markdown_table(
                ["Scenario", "Mean daily steps (95% CI)", "High-day proportion (95% CI)"],
                scenario_rows,
            ),
            "## Paired changes from baseline\n\n"
            + markdown_table(
                [
                    "Scenario",
                    "Step difference (95% CI)",
                    "High-day difference, pp (95% CI)",
                ],
                effect_rows,
            ),
            "These intervention effects are hypothetical model-sensitivity results, not causal estimates from observed treatment data.",
        ]
    )
    (outputs / "report_tables.md").write_text(report_tables + "\n", encoding="utf-8")
    print("Generated three report figures and outputs/report_tables.md")


if __name__ == "__main__":
    main()
