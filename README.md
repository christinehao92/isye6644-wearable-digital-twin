# ISyE 6644 Wearable Digital Twin Project

## Project topic

Topic #1 - Digital Twins

## Team members

- YueHao
- Zikun Li

## Project objective

This project develops a simulation-based personal wellness digital twin from public Fitbit activity data. The model represents each observed person-day as a daily activity state, estimates how those states change from one day to the next, and simulates baseline and behavioral-intervention scenarios.

Working research question:

> How does a Fitbit-calibrated daily activity-state digital twin respond to simulated behavioral interventions that increase movement?

The project is a wellness simulation and does not make medical diagnoses or clinical recommendations.

## Data

The local raw-data folders are:

- `Fitabase Data 3.12.16-4.11.16/`
- `Fitabase Data 4.12.16-5.12.16/`

The primary inputs are the two `dailyActivity_merged.csv` files. The second period's `sleepDay_merged.csv` may be used for an optional sleep/activity analysis. Raw data are intentionally excluded from Git.

Public source: [FitBit Fitness Tracker Data on Kaggle](https://www.kaggle.com/datasets/arashnic/fitbit), published under CC0: Public Domain. The dataset page describes records from 30 eligible Fitbit users who consented to provide personal tracker data. The self-contained submission ZIP includes only the two small daily-activity files actually used by this analysis.

## Planned workflow

1. Audit participant coverage, dates, duplicates, and missing values.
2. Combine and clean the two daily-activity files.
3. Define interpretable daily activity states.
4. Estimate participant-aware transition probabilities.
5. Validate the fitted model against empirical results.
6. Simulate a baseline and clearly defined interventions.
7. Compare scenarios using replicated experiments and confidence intervals.
8. Regenerate all final tables and figures from code.

## Repository layout

```text
config/       Model and experiment settings
figures/      Generated report figures
notebooks/    Optional exploratory notebooks
outputs/      Generated tables and simulation results
references/   Source notes and citation records
report/       Student-authored report materials
scripts/      Command-line entry points
src/          Reusable Python package
tests/        Automated checks
```

## File guide

- `config/project.json`: approved state thresholds, seed, horizon, replications, and scenarios.
- `src/wearable_twin/data.py`: source discovery, schema validation, overlap resolution, and audit calculations.
- `src/wearable_twin/model.py`: activity-state assignment, transition estimation, bootstrap intervals, and holdout validation.
- `src/wearable_twin/simulation.py`: intervention transformation, replicated Markov simulation, confidence intervals, paired comparisons, and analytical verification.
- `src/wearable_twin/plotting.py`: report figure generation.
- `scripts/01_audit_data.py`: creates the cleaned daily dataset and audit summary.
- `scripts/02_fit_transition_model.py`: creates transition estimates, intervals, and validation results.
- `scripts/03_run_simulation.py`: runs all baseline and intervention replications.
- `scripts/04_generate_report_assets.py`: creates figures and consolidated report tables.
- `scripts/05_build_submission.py`: builds and audits the code-submission ZIP.
- `scripts/run_all.py`: runs analysis stages 01 through 04 in order.
- `tests/`: nine automated tests for cleaning, modeling, and simulation behavior.
- `references/MODEL_DECISIONS.md`: modeling assumptions, rationale, limitations, and verified numerical results.
- `references/DATA_SOURCE.md`: dataset provenance and usage notes.
- `AI_USAGE.md`: detailed generative-AI assistance log for student review and disclosure.

## Setup

From PowerShell in the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Run the complete analysis pipeline with:

```powershell
py scripts/run_all.py
```

The command above runs the complete analysis in order. To run individual stages:

```powershell
py scripts/01_audit_data.py
py scripts/02_fit_transition_model.py
py scripts/03_run_simulation.py
py scripts/04_generate_report_assets.py
py -m unittest discover -s tests -v
```

These commands create the cleaned daily dataset, audit summary, activity states,
transition counts and probabilities, participant-bootstrap confidence intervals,
and chronological validation results under `outputs/`. Generated artifacts are
intentionally ignored by Git. The simulation stage adds replication-level
results, scenario summaries, paired comparisons, scenario transition matrices,
and analytical validation results.

Report-ready figures are generated as:

- `figures/transition_matrix.png`
- `figures/scenario_outcomes.png`
- `figures/paired_effects.png`

Consolidated result tables are generated in `outputs/report_tables.md`.

Build the self-contained code submission after running the pipeline:

```powershell
py scripts/05_build_submission.py
```

The ZIP is written to `submission/isye6644-wearable-digital-twin-code.zip`.

## Reproducibility

- Raw source data remain unchanged.
- Generated files are written only to `outputs/` and `figures/`.
- Random-number seeds and replication settings live in `config/project.json`.
- Every reported table and figure must be reproducible from the submitted code.

## Academic-integrity note

This repository includes `AI_USAGE.md` so all generative-AI assistance can be disclosed precisely. The students remain responsible for the modeling decisions, interpretation, final writing, and compliance with course policy.
