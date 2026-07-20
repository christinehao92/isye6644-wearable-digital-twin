# Data Source and Provenance

## Dataset

FitBit Fitness Tracker Data, published on Kaggle by Möbius:

https://www.kaggle.com/datasets/arashnic/fitbit

Access checked: 2026-07-20.

The Kaggle page identifies the license as CC0: Public Domain and describes personal fitness-tracker data from 30 eligible Fitbit users who consented to provide minute-level physical activity, heart-rate, and sleep-monitoring data.

## Files used

This project uses only:

- `Fitabase Data 3.12.16-4.11.16/dailyActivity_merged.csv`
- `Fitabase Data 4.12.16-5.12.16/dailyActivity_merged.csv`

The two files contain daily steps, distance, activity minutes, sedentary minutes, and calories. The code retains source-period provenance and resolves the conflicting April 12 overlap using the later-period records, as documented in `MODEL_DECISIONS.md`.

## Scope

The data are observational and anonymized. They do not establish causal effects of behavioral interventions and are not used for medical diagnosis. The simulated promotion scenarios are hypothetical sensitivity experiments.
