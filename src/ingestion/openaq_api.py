import csv
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Raw air-quality data folder
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "air_quality"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAQ_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAQ_API_KEY not found in .env file."
    )


# OpenAQ API authentication
headers = {
    "X-API-Key": api_key
}


# OpenAQ locations API
LOCATIONS_URL = "https://api.openaq.org/v3/locations"


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


# CSV columns
fieldnames = [
    "timestamp",
    "city",
    "location_id",
    "sensor_id",
    "parameter",
    "value",
    "latitude",
    "longitude"
]


def find_location(latitude, longitude):

    params = {
        "coordinates": f"{latitude},{longitude}",
        "radius": 25000,
        "limit": 10
    }

    response = requests.get(
        LOCATIONS_URL,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    locations = data.get(
        "results",
        []
    )

    if not locations:
        return None

    return locations[0]


def get_sensors(location_id):

    url = (
        f"https://api.openaq.org/v3/"
        f"locations/{location_id}/sensors"
    )

    response = requests.get(
        url,
        headers=headers,
        params={"limit": 100},
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "results",
        []
    )


def get_latest_measurements(location_id):

    url = (
        f"https://api.openaq.org/v3/"
        f"locations/{location_id}/latest"
    )

    response = requests.get(
        url,
        headers=headers,
        params={"limit": 100},
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "results",
        []
    )


for city in cities:

    city_name = city["city"]

    print(
        f"\nSearching OpenAQ location for {city_name}..."
    )

    try:

        # --------------------------------------------------
        # Find monitoring location
        # --------------------------------------------------

        location = find_location(
            city["latitude"],
            city["longitude"]
        )

        if location is None:

            print(
                f"No OpenAQ location found for {city_name}"
            )

            continue

        location_id = location["id"]

        print(
            f"Location found: {location_id}"
        )


        # --------------------------------------------------
        # Get sensor metadata
        # --------------------------------------------------

        sensors = get_sensors(
            location_id
        )

        sensor_info = {}

        for sensor in sensors:

            sensor_id = sensor["id"]

            parameter = sensor.get(
                "parameter",
                {}
            )

            sensor_info[sensor_id] = {
                "parameter": parameter.get(
                    "name",
                    "unknown"
                ),
                "unit": parameter.get(
                    "units",
                    ""
                )
            }


        # --------------------------------------------------
        # Get latest measurements
        # --------------------------------------------------

        measurements = get_latest_measurements(
            location_id
        )

        if not measurements:

            print(
                f"No measurements found for {city_name}"
            )

            continue


        # --------------------------------------------------
        # Output file
        # --------------------------------------------------

        output_file = (
            OUTPUT_DIR /
            f"{city_name}.csv"
        )


        # --------------------------------------------------
        # Read existing records
        # --------------------------------------------------

        existing_records = set()

        if output_file.exists():

            with open(
                output_file,
                "r",
                newline="",
                encoding="utf-8"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    record_key = (
                        row["timestamp"],
                        row["sensor_id"]
                    )

                    existing_records.add(
                        record_key
                    )


        file_exists = output_file.exists()

        new_records = 0


        # --------------------------------------------------
        # Append new measurements
        # --------------------------------------------------

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


            # Write header for new/empty file
            if (
                not file_exists
                or output_file.stat().st_size == 0
            ):

                writer.writeheader()


            for measurement in measurements:

                sensor_id = measurement.get(
                    "sensorsId"
                )

                if sensor_id is None:
                    continue


                # Get parameter + unit
                info = sensor_info.get(
                    sensor_id
                )

                if info is None:

                    print(
                        f"Sensor metadata not found: "
                        f"{sensor_id}"
                    )

                    continue


                parameter = info["parameter"]

                unit = info["unit"]


                # --------------------------------------------------
                # Timestamp
                # --------------------------------------------------

                datetime_info = measurement.get(
                    "datetime",
                    {}
                )

                timestamp = datetime_info.get(
                    "local"
                )

                if not timestamp:
                    continue

                timestamp = (
                    timestamp
                    .replace("T", " ")
                    [:16]
                )


                # --------------------------------------------------
                # Measurement value
                # --------------------------------------------------

                value = measurement.get(
                    "value"
                )

                if value is None:
                    continue


                # Add unit directly to the value
                if unit:

                    value_with_unit = (
                        f"{value} {unit}"
                    )

                else:

                    value_with_unit = str(
                        value
                    )


                # --------------------------------------------------
                # Coordinates
                # --------------------------------------------------

                coordinates = measurement.get(
                    "coordinates",
                    {}
                )

                latitude = coordinates.get(
                    "latitude"
                )

                longitude = coordinates.get(
                    "longitude"
                )


                # --------------------------------------------------
                # Duplicate check
                # --------------------------------------------------

                record_key = (
                    timestamp,
                    str(sensor_id)
                )

                if record_key in existing_records:
                    continue


                # --------------------------------------------------
                # Write record
                # --------------------------------------------------

                writer.writerow({

                    "timestamp": timestamp,

                    "city": city_name,

                    "location_id": location_id,

                    "sensor_id": sensor_id,

                    "parameter": parameter,

                    "value": value_with_unit,

                    "latitude": latitude,

                    "longitude": longitude
                })


                existing_records.add(
                    record_key
                )

                new_records += 1


        print(
            f"New measurements added: "
            f"{new_records}"
        )

        print(
            f"Saved → {output_file.name}"
        )


    except requests.exceptions.RequestException as error:

        print(
            f"API error for {city_name}: {error}"
        )


    except (
        KeyError,
        TypeError,
        ValueError
    ) as error:

        print(
            f"Data error for {city_name}: {error}"
        )


print(
    "\nAir-quality ingestion completed."
)