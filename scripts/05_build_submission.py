"""Build and audit the self-contained code-submission ZIP."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_DIR = PROJECT_ROOT / "submission"
ARCHIVE_PATH = SUBMISSION_DIR / "isye6644-wearable-digital-twin-code.zip"
ARCHIVE_ROOT = "isye6644-wearable-digital-twin"

FILES = [
    "README.md",
    "requirements.txt",
    "AI_USAGE.md",
    "config/project.json",
    "references/DATA_SOURCE.md",
    "references/MODEL_DECISIONS.md",
    "Fitabase Data 3.12.16-4.11.16/dailyActivity_merged.csv",
    "Fitabase Data 4.12.16-5.12.16/dailyActivity_merged.csv",
    "figures/transition_matrix.png",
    "figures/scenario_outcomes.png",
    "figures/paired_effects.png",
    "outputs/data_audit.json",
    "outputs/report_tables.md",
    "outputs/transition_matrix.csv",
    "outputs/transition_intervals.csv",
    "outputs/transition_validation.json",
    "outputs/simulation_summary.csv",
    "outputs/paired_comparisons.csv",
    "outputs/simulation_validation.csv",
]
DIRECTORIES = ["src", "scripts", "tests"]
BANNED_PARTS = {".git", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
BANNED_SUFFIXES = {".pyc", ".pyo"}


def collect_files() -> list[Path]:
    selected = [PROJECT_ROOT / relative for relative in FILES]
    for directory in DIRECTORIES:
        selected.extend((PROJECT_ROOT / directory).rglob("*.py"))

    missing = [str(path.relative_to(PROJECT_ROOT)) for path in selected if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Run the complete pipeline before packaging. Missing files: "
            + ", ".join(missing)
        )

    unique = sorted(set(selected), key=lambda path: path.as_posix().lower())
    for path in unique:
        relative = path.relative_to(PROJECT_ROOT)
        if BANNED_PARTS.intersection(relative.parts) or path.suffix in BANNED_SUFFIXES:
            raise ValueError(f"Banned file selected for submission: {relative}")
    return unique


def build_archive() -> list[str]:
    selected = collect_files()
    SUBMISSION_DIR.mkdir(exist_ok=True)
    temporary_archive = ARCHIVE_PATH.with_suffix(".tmp.zip")
    if temporary_archive.exists():
        temporary_archive.unlink()

    with zipfile.ZipFile(
        temporary_archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in selected:
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            archive.write(path, f"{ARCHIVE_ROOT}/{relative}")

    with zipfile.ZipFile(temporary_archive) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise RuntimeError(f"ZIP integrity check failed at {bad_member}")
        members = archive.namelist()

    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()
    shutil.move(temporary_archive, ARCHIVE_PATH)
    return members


def main() -> None:
    members = build_archive()
    print(f"Created {ARCHIVE_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Files: {len(members)}")
    print(f"Size: {ARCHIVE_PATH.stat().st_size / 1024:.1f} KiB")
    print("ZIP integrity check: passed")


if __name__ == "__main__":
    main()
