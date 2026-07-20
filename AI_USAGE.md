# Generative AI Usage Log

This file is a working log for the precise disclosure required by the ISyE 6644 project guidance. The students must review it, correct it, and include an appropriate disclosure with the final submission.

## Tool

- OpenAI Codex, accessed through the Codex desktop application.

## Assistance provided

- Reviewed the project-guidance document and summarized submission constraints.
- Recovered decisions from a user-provided shared ChatGPT conversation.
- Helped organize the Git repository and submission-oriented project structure.
- Proposed a reproducible Python workflow for data auditing, model fitting, simulation, verification, and packaging.

## Student responsibility

YueHao and Zikun Li are responsible for approving the research question, choosing and defending modeling assumptions, reviewing and understanding all code, interpreting results, writing the final report in their own words, verifying citations, and ensuring that the submitted work complies with the course's AI policy.

## Updates required

Add a dated entry whenever AI assistance materially changes code, analysis, figures, or wording. Describe the exact task and the student's verification rather than using a generic statement such as "AI was used for editing."

## Work log

### 2026-07-20

- Codex created the initial repository scaffold, dependency list, configuration file, reusable data-loading/cleaning module, command-line data-audit script, and two automated cleaning tests.
- Codex identified 24 conflicting April 12 participant-day overlaps. The implemented rule retains the later-period record because the earlier-period April 12 observations appear incomplete: their mean step count is 1,761.6 compared with 8,236.8 in the later file.
- The students must review the code, run it themselves, and approve or revise the proposed activity-state definition before it is used in the model.
- After user approval, Codex implemented the three-state assignment, consecutive-day transition construction, participant-level bootstrap confidence intervals, chronological holdout validation, a command-line fitting script, and three additional automated tests.
- The generated transition results were checked for probability normalization and compared against a state-frequency baseline. The students remain responsible for interpreting these results and explaining the Markov assumptions in their own words.
- Codex implemented the replicated Markov simulator, hypothetical promotion scenarios, common-random-number pairing, normal-theory confidence intervals, exact finite-horizon validation, an experiment runner, and four additional automated checks. The students must not describe the hypothetical promotion probabilities as observed or causal intervention effects.
- Codex implemented the reproducible figure-generation module, consolidated table generator, and one-command pipeline runner. Codex visually checked all three generated figures for readable labels, axes, confidence intervals, spacing, and clipping. The students must decide which figures to include and must write their own surrounding interpretation.
- Codex verified the public Kaggle dataset page and CC0 license, added dataset-provenance documentation, expanded the README file guide, and implemented a deterministic submission packager that includes only required inputs, code, tests, selected outputs, and figures while excluding Git history, caches, course documents, and unused raw files.
- Codex extracted the code-submission ZIP into a clean temporary directory, created a new virtual environment, installed only `requirements.txt`, reran all nine tests, and reproduced the complete four-stage pipeline successfully. Codex also audited the archive for integrity and prohibited or irrelevant files.
