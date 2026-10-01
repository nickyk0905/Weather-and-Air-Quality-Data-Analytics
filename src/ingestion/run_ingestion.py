import subprocess
import sys
from pathlib import Path


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PYTHON = sys.executable


scripts = [
    PROJECT_ROOT / "src" / "ingestion" / "weather_api.py",
    PROJECT_ROOT / "src" / "ingestion" / "openaq_api.py",
]


for script in scripts:

    print("\n" + "=" * 60)
    print(f"Running: {script.name}")
    print("=" * 60)

    result = subprocess.run(
        [PYTHON, str(script)],
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:

        print(
            f"\nERROR: {script.name} failed."
        )

        sys.exit(
            result.returncode
        )


print("\n" + "=" * 60)
print("ALL INGESTION JOBS COMPLETED SUCCESSFULLY")
print("=" * 60)