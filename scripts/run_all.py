"""Run the complete reproducible analysis pipeline in order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    "01_audit_data.py",
    "02_fit_transition_model.py",
    "03_run_simulation.py",
    "04_generate_report_assets.py",
]


def main() -> None:
    for stage in STAGES:
        print(f"\n=== Running {stage} ===", flush=True)
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / stage)],
            cwd=PROJECT_ROOT,
            check=True,
        )
    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
