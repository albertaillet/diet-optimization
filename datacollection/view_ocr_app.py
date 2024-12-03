import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path

import certifi
import requests
from flask import Flask, abort, jsonify, render_template, send_from_directory

from datacollection.database import Database, ImageData
from datacollection.init_db import validate_db
from datacollection.run_ocr import run_ocr_on_image_paths
from utils.image import image_info

DATA_DIR = Path(os.getenv("DATA_DIR", "")).resolve()
BASE_IMAGE_DIR = DATA_DIR / "exported_images"


def check_ean13(num_str: str) -> bool:
    """Based on https://en.wikipedia.org/wiki/International_Article_Number#Position_%E2%80%93_weight."""
    if len(num_str) != 13:
        return False
    remainder = sum(int(num_str[i]) * (3 if i % 2 else 1) for i in range(12)) % 10
    check_digit = 10 - remainder if remainder else 0
    return int(num_str[-1]) == check_digit


def get_annotations_from_file(annotation_file: Path) -> list[str]:
    """Get OCR annotations from a JSON file."""
    if not annotation_file.exists():
        return []

    with annotation_file.open("r") as f:
        data = json.load(f)
        responses = data.get("responses", [])
        if not responses:
            return []
        return [ann["description"] for ann in responses[0].get("textAnnotations", [])]


def extract_longest_number(annotations: list[str]) -> str:
    """Extract the longest numeric string from annotations."""
    longest = ""
    for text in annotations:
        numbers = re.findall(r"\d+", text)
        if numbers:
            for num in numbers:
                if len(num) > len(longest):
                    longest = num
    return longest


def find_ean_in_annotations(annotation_file: Path) -> str | None:
    """Find valid EAN-13 in OCR annotations."""
    annotations = get_annotations_from_file(annotation_file)
    if not annotations:
        return None

    longest_number = extract_longest_number(annotations)
    if len(longest_number) == 13 and check_ean13(longest_number):
        return longest_number
    return None


def update_eans_from_annotations(db: Database, list_of_file_names: list[str]) -> None:
    """Update database with EANs found in OCR annotations."""
    print("Checking for EANs in OCR annotations...")
    eans_found = 0

    for name in list_of_file_names:
        image_data = db.get_image_data(name)
        if image_data and not image_data.ean:  # Only check if EAN is not already set
            ean = find_ean_in_annotations(BASE_IMAGE_DIR / f"{name}.json")
            if ean:
                db.update_ean(name, ean)
                eans_found += 1
                print(f"Found EAN {ean} for {name}")

    if eans_found:
        print(f"Added {eans_found} EANs from OCR annotations")
    else:
        print("No new EANs found in OCR annotations")


def create_app(list_of_file_names: list[str], db: Database) -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        columns = [
            {"key": "image_name", "title": "Image Name", "filterable": True},
            {"key": "ean", "title": "EAN", "filterable": True, "not_none_filter": True},
            {"key": "latitude", "title": "Latitude", "filterable": True},
            {"key": "longitude", "title": "Longitude", "filterable": True},
            {"key": "created_at", "title": "Created At", "filterable": True},
            {"key": "last_updated", "title": "Last Updated", "filterable": True},
        ]
        images = db.get_all_images()
        return render_template("index.html", images=images, columns=columns)

    @app.route("/images/<path:image_filename>")
    def serve_image(image_filename: str):
        return send_from_directory(BASE_IMAGE_DIR, image_filename)

    @app.route("/<name>")
    def image_page(name: str):
        image_file = BASE_IMAGE_DIR / f"{name}.png"
        annotation_file = BASE_IMAGE_DIR / f"{name}.json"

        if not image_file.exists():
            abort(404)

        stored_data = db.get_image_data(name)
        gps_info, date_info = image_info(image_file)

        annotations = get_annotations_from_file(annotation_file)

        # Extract the longest numeric string if we have annotations
        longest_number = extract_longest_number(annotations) if annotations else ""

        # Use stored EAN if available, otherwise use the detected one
        ean = stored_data.ean if stored_data else (longest_number if len(longest_number) == 13 else "")

        # Store initial data in database if not exists
        db.insert_image_data(
            ImageData(
                image_name=name,
                ean=ean,
                latitude=gps_info.get("GPSLatitude"),
                longitude=gps_info.get("GPSLongitude"),
                created_at=date_info.get("CreateDate"),
                last_updated=datetime.now().isoformat(),
            )
        )

        i = list_of_file_names.index(name)
        return render_template(
            "image_page.html",
            name=name,
            image_file=f"/images/{name}.png",
            annotations=annotations,
            prev=list_of_file_names[i - 1],
            next=list_of_file_names[(i + 1) % len(list_of_file_names)],
            ean=ean,
            latitude=gps_info.get("GPSLatitude"),
            longitude=gps_info.get("GPSLongitude"),
            created_at=date_info.get("CreateDate"),
        )

    @app.route("/run_ocr/<name>")
    def run_ocr_route(name: str):
        image_file = BASE_IMAGE_DIR / f"{name}.png"
        if not image_file.exists():
            return jsonify({"error": "Image not found"}), 404
        try:
            session = requests.Session()
            requests.get("https://vision.googleapis.com", verify=certifi.where())
            responses, _performed_request = run_ocr_on_image_paths([image_file], session, override=True)
            if responses:
                _image_path, response = responses[0]
                with (BASE_IMAGE_DIR / f"{name}.json").open("w") as f:
                    json.dump({"responses": [response]}, f, indent=2)
                # Check if EAN can be found in annotations
                ean = find_ean_in_annotations(BASE_IMAGE_DIR / f"{name}.json")
                if ean:
                    db.update_ean(name, ean)
                return jsonify({"success": True})
            return jsonify({"error": "No response from OCR"}), 500
        except Exception as e:  # noqa: BLE001
            return jsonify({"error": str(e)}), 500

    @app.route("/validate_ean/<ean>")
    def validate_ean(ean: str):
        if not ean or not check_ean13(ean):
            return jsonify({"message": "Invalid EAN-13"}), 400
        return jsonify({"message": "Valid EAN-13"}), 200

    @app.route("/check_off/<ean>")
    def check_off(ean: str):
        if not check_ean13(ean):
            return render_template("validation_result.html", error="Invalid EAN-13")

        response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{ean}.json")
        if response.status_code == 200:
            product_data = response.json()
            if product_data.get("status") == 1:
                return render_template("validation_result.html", product=product_data.get("product"))
            return render_template("validation_result.html", error="Product not found in Open Food Facts")
        return render_template("validation_result.html", error="Error fetching data from Open Food Facts")

    @app.route("/update_ean/<name>/<ean>", methods=["POST"])
    def update_ean(name: str, ean: str):
        if db.update_ean(name, ean):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Failed to update EAN"}), 500

    return app


if __name__ == "__main__":
    list_of_file_names = sorted([p.stem for p in BASE_IMAGE_DIR.glob("*.png")])
    with (DATA_DIR / "hardcoded_locations.csv").open("r") as file:
        locations = list(csv.DictReader(file))

    db = Database(DATA_DIR / "images.db")
    validate_db(db, list_of_file_names)
    update_eans_from_annotations(db, list_of_file_names)
    app = create_app(list_of_file_names, db)
    app.run(debug=True)
