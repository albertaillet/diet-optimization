"""This script summarizes the fetched product information into a csv file.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python products_summarize.py
"""

import csv
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

DATA_DIR = Path(os.getenv("DATA_DIR", ""))
OFF_USERNAME = os.getenv("OFF_USERNAME")


def fetch_osm_coordinates(osm_id: str) -> tuple[float | None, float | None]:
    """Fetch coordinates from OpenStreetMap Overpass API."""
    url = f"https://overpass-api.de/api/interpreter?data=[out:json];node({osm_id});out;"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("elements") and len(data["elements"]) > 0:
            element = data["elements"][0]
            return element.get("lat"), element.get("lon")

        return None, None
    except requests.RequestException as e:
        print(f"Error fetching coordinates for OSM ID {osm_id}: {e}")
        return None, None


def read_all_locations(price_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Read all locations from the price items and enrich with coordinates."""
    locations = {}
    for price_item in price_items:
        location = price_item["location"]
        osm_id = location["osm_id"]

        if osm_id not in locations:
            # Add basic location info
            locations[osm_id] = location

            # Fetch and add coordinates
            print(f"Fetching coordinates for OSM ID {osm_id}...")
            lat, lon = fetch_osm_coordinates(osm_id)

            if lat is not None and lon is not None:
                locations[osm_id]["latitude"] = lat
                locations[osm_id]["longitude"] = lon
            else:
                print(f"Could not fetch coordinates for OSM ID {osm_id}")

            time.sleep(0.1)

    return locations


if __name__ == "__main__":
    assert OFF_USERNAME is not None, f"Set OFF_USERNAME env variable {OFF_USERNAME=}"

    with (DATA_DIR / "user_data" / OFF_USERNAME / "prices.json").open("r") as file:
        price_items = json.load(file)["items"]

    locations = read_all_locations(price_items)

    # Ensure output directory exists
    output_dir = DATA_DIR / "user_data" / OFF_USERNAME
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to CSV with all fields including coordinates
    with (output_dir / "locations.csv").open("w") as file:
        if locations:
            first_location = next(iter(locations.values()))
            writer = csv.DictWriter(file, fieldnames=first_location.keys())
            writer.writeheader()
            for location in locations.values():
                writer.writerow(location)
            print(f"Wrote {len(locations)} locations to {output_dir}/locations.csv")
        else:
            print("No locations to write")
