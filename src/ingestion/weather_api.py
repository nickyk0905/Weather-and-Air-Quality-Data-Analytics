import csv
from pathlib import Path

import requests


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Raw weather data folder
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "weather"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Indian cities
cities = [
    {"city": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
    {"city": "Mumbai", "latitude": 19.0760, "longitude": 72.8777},
    {"city": "Bengaluru", "latitude": 12.9716, "longitude": 77.5946},
    {"city": "Chennai", "latitude": 13.0827, "longitude": 80.2707},
    {"city": "Kolkata", "latitude": 22.5726, "longitude": 88.3639},
    {"city": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867},
    {"city": "Pune", "latitude": 18.5204, "longitude": 73.8567},
    {"city": "Ahmedabad", "latitude": 23.0225, "longitude": 72.5714},
]


# Open-Meteo API
url = "https://api.open-meteo.com/v1/forecast"


# CSV columns
fieldnames = [
    "timestamp",
    "latitude",
    "longitude",
    "temperature",
    "humidity",
    "precipitation",
    "wind_speed",
]


for city in cities:

    city_name = city["city"]

    output_file = OUTPUT_DIR / f"{city_name}.csv"

    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "wind_speed_10m"
        ),
        "timezone": "Asia/Kolkata",
    }

    print(
        f"\nFetching weather data for {city_name}..."
    )

    try:

        # Call API
        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        current = data["current"]

        timestamp = current["time"].replace(
            "T",
            " "
        )


        # --------------------------------------------------
        # Check whether this timestamp already exists
        # --------------------------------------------------

        existing_timestamps = set()

        if output_file.exists():

            with open(
                output_file,
                "r",
                newline="",
                encoding="utf-8"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    existing_timestamps.add(
                        row["timestamp"]
                    )


        # Don't insert duplicate observation
        if timestamp in existing_timestamps:

            print(
                f"Already exists: {timestamp}"
            )

            continue


        # --------------------------------------------------
        # Append data
        # --------------------------------------------------

        file_exists = output_file.exists()

        with open(
            output_file,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            # Write header only for a new/empty file
            if (
                not file_exists
                or output_file.stat().st_size == 0
            ):

                writer.writeheader()


            writer.writerow({

                "timestamp": timestamp,

                "latitude": city["latitude"],

                "longitude": city["longitude"],

                "temperature": (
                    f'{current["temperature_2m"]} °C'
                ),

                "humidity": (
                    f'{current["relative_humidity_2m"]} %'
                ),

                "precipitation": (
                    f'{current["precipitation"]} mm'
                ),

                "wind_speed": (
                    f'{current["wind_speed_10m"]} km/h'
                ),
            })


        print(
            f"Saved → {output_file.name}"
        )


    except requests.exceptions.RequestException as error:

        print(
            f"API request failed for {city_name}: {error}"
        )


    except KeyError as error:

        print(
            f"Unexpected API response for {city_name}: {error}"
        )


print(
    "\nWeather ingestion completed.\n"
)