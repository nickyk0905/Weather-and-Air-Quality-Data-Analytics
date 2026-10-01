import csv
from pathlib import Path
from datetime import datetime
import time

import requests


# --------------------------------------------------
# Project root
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------
# Raw weather data folder
# --------------------------------------------------

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "weather"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# Weather API
# --------------------------------------------------

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
)


# --------------------------------------------------
# Indian cities
# --------------------------------------------------

cities = [
    {
        "city": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    {
        "city": "Mumbai",
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    {
        "city": "Bengaluru",
        "latitude": 12.9716,
        "longitude": 77.5946
    },
    {
        "city": "Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707
    },
    {
        "city": "Kolkata",
        "latitude": 22.5726,
        "longitude": 88.3639
    },
    {
        "city": "Hyderabad",
        "latitude": 17.3850,
        "longitude": 78.4867
    },
    {
        "city": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567
    },
    {
        "city": "Ahmedabad",
        "latitude": 23.0225,
        "longitude": 72.5714
    }
]


# --------------------------------------------------
# Timestamp when ingestion starts
# --------------------------------------------------

execution_timestamp = datetime.now().strftime(
    "%Y-%m-%d %H:%M"
)

print(
    f"\nWeather ingestion started at: "
    f"{execution_timestamp}"
)


# --------------------------------------------------
# API request with retry mechanism
# --------------------------------------------------

def make_request(
    url,
    params,
    retries=3,
    delay=5
):

    for attempt in range(1, retries + 1):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            return response

        except requests.exceptions.RequestException as error:

            print(
                f"Request failed "
                f"(attempt {attempt}/{retries}): "
                f"{error}"
            )

            if attempt < retries:

                print(
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

    return None


# --------------------------------------------------
# Process each city
# --------------------------------------------------

for city in cities:

    city_name = city["city"]

    print(
        f"\nFetching weather data for "
        f"{city_name}..."
    )

    params = {

        "latitude":
            city["latitude"],

        "longitude":
            city["longitude"],

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "wind_speed_10m"
        ),

        "timezone":
            "Asia/Kolkata"
    }


    # --------------------------------------------------
    # API request
    # --------------------------------------------------

    response = make_request(
        WEATHER_URL,
        params
    )

    if response is None:

        print(
            f"Weather API failed for "
            f"{city_name} after 3 attempts."
        )

        continue


    try:

        data = response.json()

        current = data["current"]


        # --------------------------------------------------
        # Open city CSV
        # --------------------------------------------------

        output_file = (
            OUTPUT_DIR
            / f"{city_name}.csv"
        )


        # --------------------------------------------------
        # Read existing timestamps
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


        # --------------------------------------------------
        # API observation timestamp
        # --------------------------------------------------

        api_timestamp = current["time"]

        timestamp = api_timestamp.replace(
            "T",
            " "
        )


        # --------------------------------------------------
        # Duplicate check
        # --------------------------------------------------

        if timestamp in existing_timestamps:

            print(
                f"Data already exists for "
                f"{city_name} at {timestamp}"
            )

            continue


        # --------------------------------------------------
        # Write data
        # --------------------------------------------------

        fieldnames = [
            "timestamp",
            "latitude",
            "longitude",
            "temperature",
            "humidity",
            "precipitation",
            "wind_speed"
        ]


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


            if (
                not file_exists
                or output_file.stat().st_size == 0
            ):

                writer.writeheader()


            writer.writerow({

                "timestamp":
                    timestamp,

                "latitude":
                    city["latitude"],

                "longitude":
                    city["longitude"],

                "temperature":
                    f'{current["temperature_2m"]} °C',

                "humidity":
                    f'{current["relative_humidity_2m"]} %',

                "precipitation":
                    f'{current["precipitation"]} mm',

                "wind_speed":
                    f'{current["wind_speed_10m"]} km/h'
            })


        print(
            f"Weather data added for "
            f"{city_name}"
        )

        print(
            f"Saved → {output_file.name}"
        )


    except (
        KeyError,
        TypeError,
        ValueError
    ) as error:

        print(
            f"Data processing error for "
            f"{city_name}: {error}"
        )


print(
    "\nWeather ingestion completed.\n"
)