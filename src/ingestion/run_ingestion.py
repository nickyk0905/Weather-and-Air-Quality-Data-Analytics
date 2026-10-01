from datetime import datetime
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PYTHON = sys.executable

current_time = datetime.now()


# --------------------------------
# AIR QUALITY
# --------------------------------

print("\n" + "=" * 60)
print("Running: openaq_api.py")
print("=" * 60)

result = subprocess.run(
    [
        PYTHON,
        str(
            PROJECT_ROOT
            / "src"
            / "ingestion"
            / "openaq_api.py"
        )
    ],
    cwd=PROJECT_ROOT
)

if result.returncode != 0:
    print("\nERROR: openaq_api.py failed.")
    sys.exit(result.returncode)


# --------------------------------
# WEATHER
# --------------------------------

if current_time.hour == 10 and current_time.minute < 5:

    print("\n" + "=" * 60)
    print("10:00 AM detected.")
    print("Running: weather_api.py")
    print("=" * 60)

    result = subprocess.run(
        [
            PYTHON,
            str(
                PROJECT_ROOT
                / "src"
                / "ingestion"
                / "weather_api.py"
            )
        ],
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        print("\nERROR: weather_api.py failed.")
        sys.exit(result.returncode)

else:

    print(
        f"\nCurrent time: "
        f"{current_time.strftime('%H:%M')}"
    )

    print(
        "Weather ingestion skipped. "
        "It runs only at 10:00 AM."
    )


print("\n" + "=" * 60)
print("INGESTION CYCLE COMPLETED")
print("=" * 60)
print()