"""Load, validate, audit, and clean the Fitbit daily activity data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


DAILY_ACTIVITY_FILENAME = "dailyActivity_merged.csv"
KEY_COLUMNS = ["Id", "ActivityDate"]
NUMERIC_COLUMNS = [
    "TotalSteps",
    "TotalDistance",
    "TrackerDistance",
    "LoggedActivitiesDistance",
    "VeryActiveDistance",
    "ModeratelyActiveDistance",
    "LightActiveDistance",
    "SedentaryActiveDistance",
    "VeryActiveMinutes",
    "FairlyActiveMinutes",
    "LightlyActiveMinutes",
    "SedentaryMinutes",
    "Calories",
]
REQUIRED_COLUMNS = KEY_COLUMNS + NUMERIC_COLUMNS


def find_daily_activity_files(project_root: Path) -> list[Path]:
    """Return raw daily-activity files in chronological folder order."""
    files = sorted(project_root.glob(f"Fitabase Data */{DAILY_ACTIVITY_FILENAME}"))
    if not files:
        raise FileNotFoundError(
            f"No {DAILY_ACTIVITY_FILENAME} files found under {project_root}"
        )
    return files


def load_daily_activity(project_root: Path) -> pd.DataFrame:
    """Load every daily-activity period and retain source provenance."""
    frames: list[pd.DataFrame] = []
    for priority, path in enumerate(find_daily_activity_files(project_root)):
        frame = pd.read_csv(path, dtype={"Id": "string"})
        missing_columns = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
        if missing_columns:
            raise ValueError(f"{path} is missing columns: {missing_columns}")

        frame = frame[REQUIRED_COLUMNS].copy()
        frame["ActivityDate"] = pd.to_datetime(
            frame["ActivityDate"], format="%m/%d/%Y", errors="raise"
        )
        frame[NUMERIC_COLUMNS] = frame[NUMERIC_COLUMNS].apply(
            pd.to_numeric, errors="raise"
        )
        frame["SourcePeriod"] = path.parent.name
        frame["_SourcePriority"] = priority
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def clean_daily_activity(raw: pd.DataFrame) -> pd.DataFrame:
    """Validate daily records and resolve overlapping periods deterministically.

    The later source period wins when the same participant/date appears more than
    once. In this dataset the earlier file's April 12 records are partial-day
    observations, while the later file contains the fuller April 12 records.
    """
    missing_columns = sorted(set(REQUIRED_COLUMNS + ["_SourcePriority"]) - set(raw))
    if missing_columns:
        raise ValueError(f"Daily activity data are missing columns: {missing_columns}")
    if raw[KEY_COLUMNS].isna().any().any():
        raise ValueError("Participant IDs and activity dates cannot be missing")
    if raw[NUMERIC_COLUMNS].isna().any().any():
        raise ValueError("Daily activity numeric fields cannot be missing")
    if (raw[NUMERIC_COLUMNS] < 0).any().any():
        raise ValueError("Daily activity numeric fields cannot be negative")

    cleaned = (
        raw.sort_values(KEY_COLUMNS + ["_SourcePriority"])
        .drop_duplicates(KEY_COLUMNS, keep="last")
        .sort_values(KEY_COLUMNS)
        .reset_index(drop=True)
    )
    if cleaned.duplicated(KEY_COLUMNS).any():
        raise AssertionError("Cleaning did not produce unique participant-days")

    cleaned["ActiveMinutes"] = (
        cleaned["VeryActiveMinutes"]
        + cleaned["FairlyActiveMinutes"]
        + cleaned["LightlyActiveMinutes"]
    )
    cleaned["RecordedMinutes"] = cleaned["ActiveMinutes"] + cleaned["SedentaryMinutes"]
    cleaned["IsZeroStepDay"] = cleaned["TotalSteps"].eq(0)
    return cleaned.drop(columns="_SourcePriority")


def build_audit(raw: pd.DataFrame, cleaned: pd.DataFrame) -> dict[str, Any]:
    """Create a JSON-serializable audit summary."""
    source_summaries = []
    for source, group in raw.groupby("SourcePeriod", sort=True):
        source_summaries.append(
            {
                "source_period": source,
                "rows": int(len(group)),
                "participants": int(group["Id"].nunique()),
                "start_date": group["ActivityDate"].min().date().isoformat(),
                "end_date": group["ActivityDate"].max().date().isoformat(),
                "duplicate_person_days_within_source": int(
                    group.duplicated(KEY_COLUMNS).sum()
                ),
            }
        )

    ordered = cleaned.sort_values(KEY_COLUMNS).copy()
    ordered["PreviousDate"] = ordered.groupby("Id")["ActivityDate"].shift()
    consecutive_pairs = ordered["ActivityDate"].sub(ordered["PreviousDate"]).dt.days.eq(1)

    return {
        "sources": source_summaries,
        "combined_rows_before_overlap_resolution": int(len(raw)),
        "rows_after_overlap_resolution": int(len(cleaned)),
        "cross_source_rows_removed": int(len(raw) - len(cleaned)),
        "participants": int(cleaned["Id"].nunique()),
        "start_date": cleaned["ActivityDate"].min().date().isoformat(),
        "end_date": cleaned["ActivityDate"].max().date().isoformat(),
        "missing_cells_in_required_fields": int(
            raw[REQUIRED_COLUMNS].isna().sum().sum()
        ),
        "negative_numeric_values": int((raw[NUMERIC_COLUMNS] < 0).sum().sum()),
        "zero_step_days_after_cleaning": int(cleaned["IsZeroStepDay"].sum()),
        "available_consecutive_day_pairs": int(consecutive_pairs.sum()),
    }
