# Model Decision Log

This file records assumptions that affect the simulation. Each proposed decision must be reviewed by the students before final submission.

## D-001: Overlapping April 12 records

Status: Implemented; student review required.

The two raw daily-activity files overlap on April 12, 2016. They contain 24 duplicate participant/date keys, and all 24 pairs have conflicting measurements. The cleaning pipeline keeps the later-period version.

Reason: the earlier file's April 12 records appear to be incomplete partial-day observations. Across the overlap, the earlier version averages 1,761.6 steps and the later version averages 8,236.8 steps. Retaining the later version prevents a systematic low-activity bias at the file boundary.

## D-002: Daily activity states

Status: Approved by the user on 2026-07-20.

Proposed states based on daily steps:

- Low: fewer than 5,000 steps
- Moderate: 5,000 through 9,999 steps
- High: at least 10,000 steps

Zero-step days would be treated as unavailable activity observations rather than as genuine low-activity days. With that rule, the data contain 1,240 usable days and 1,159 consecutive-day transition pairs. The proposed state distribution is 28.0% Low, 37.3% Moderate, and 34.7% High.

Reason: the thresholds are interpretable and produce enough observations in every state for transition estimation. The final report must cite an appropriate source for any health-related interpretation and should include a sensitivity check because daily aggregates cannot conclusively distinguish non-wear from a truly inactive day.

## D-003: Population transition model

Status: Implemented and automatically tested; student interpretation required.

The model uses a first-order, time-homogeneous Markov chain estimated from 1,159 consecutive-day observations. Nonconsecutive observations do not create transitions. The fitted probability matrix is:

| Current state | Next Low | Next Moderate | Next High |
|---|---:|---:|---:|
| Low | 0.5272 | 0.3741 | 0.0986 |
| Moderate | 0.2602 | 0.5498 | 0.1900 |
| High | 0.0804 | 0.2080 | 0.7116 |

Participant-level cluster bootstrap intervals quantify uncertainty without treating every day as independent. Chronological validation uses the first 75% of transition dates for training and later dates for testing. Test log loss is 0.9437 for the transition model versus 1.0853 for a baseline that ignores current state, an improvement of 0.1416. Test classification accuracy is 0.5811.

Limitations: the model pools participants, assumes the next state depends only on the current state, and assumes transition probabilities are stable across the study period. These assumptions must be discussed and tested where feasible.

## D-004: Hypothetical intervention mechanism

Status: Implemented as a sensitivity experiment; student interpretation required.

Four 30-day scenarios use 1,000 replications and random-number seed 6644:

- Baseline: no promotion
- Light: 5% promotion probability
- Moderate: 10% promotion probability
- Strong: 15% promotion probability

After each baseline transition, the intervention has the stated hypothetical probability of promoting the resulting state by one level: Low to Moderate or Moderate to High. High remains High. This mechanism is not estimated from treatment data and must not be presented as a real intervention effect. It is a controlled sensitivity parameter for demonstrating simulation-based decision comparison.

All scenarios use common random numbers. Comparisons with baseline therefore use paired replication differences and 95% confidence intervals.

Selected results:

| Scenario | Mean daily steps (95% CI) | High-day proportion (95% CI) |
|---|---:|---:|
| Baseline | 8,219 (8,130, 8,309) | 0.349 (0.339, 0.359) |
| Light | 8,563 (8,475, 8,651) | 0.387 (0.377, 0.396) |
| Moderate | 8,908 (8,822, 8,993) | 0.425 (0.416, 0.435) |
| Strong | 9,236 (9,150, 9,322) | 0.463 (0.453, 0.473) |

The paired mean-step differences from baseline are 343 steps/day for Light (95% CI: 317, 370), 688 for Moderate (651, 726), and 1,017 for Strong (971, 1,063). These quantify model sensitivity to the hypothetical promotion parameter, not causal effects in people.

Simulation verification compares every Monte Carlo scenario/metric estimate with its exact finite-horizon Markov expectation. All 16 exact expectations fall inside their corresponding 95% Monte Carlo intervals.
