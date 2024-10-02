import json
import os
import re
from pathlib import Path

import requests
from flask import Flask, abort, jsonify, render_template, send_from_directory

from utils.image import image_info

DATA_DIR = Path(os.getenv("DATA_DIR", "")).resolve()
BASE_IMAGE_DIR = DATA_DIR / "exported_images"


# Use this function to validate EAN-13 numbers
def check_ean13(num_str: str) -> bool:
    """Based on https://en.wikipedia.org/wiki/International_Article_Number#Position_%E2%80%93_weight."""
    if len(num_str) != 13:
        return False
    remainder = sum(int(num_str[i]) * (3 if i % 2 else 1) for i in range(12)) % 10
    check_digit = 10 - remainder if remainder else 0
    return int(num_str[-1]) == check_digit


# Extract the longest numeric string from annotations
def extract_longest_number(annotations: list) -> str:
    longest = ""
    for text in annotations:
        numbers = re.findall(r"\d+", text)
        if numbers:
            for num in numbers:
                if len(num) > len(longest):
                    longest = num
    return longest


# Route to validate EAN-13 and check with Open Food Facts
def create_app(list_of_file_names: list[str]) -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("index.html", names=list_of_file_names)

    @app.route("/images/<path:image_filename>")
    def serve_image(image_filename: str):
        return send_from_directory(BASE_IMAGE_DIR, image_filename)

    @app.route("/<name>")
    def image_page(name: str):
        image_file = BASE_IMAGE_DIR / f"{name}.png"
        annotation_file = BASE_IMAGE_DIR / f"{name}.json"

        if not image_file.exists() or not annotation_file.exists():
            abort(404)

        gps_info, date_info = image_info(image_file)

        with annotation_file.open("r") as f:
            data = json.load(f)

        responses = data.get("responses", [])
        if len(responses) != 1:
            return jsonify({"error": "Invalid response length"}), 400

        annotations = responses[0].get("textAnnotations", [])
        annotation_descriptions = [ann["description"] for ann in annotations]

        # Extract the longest numeric string
        longest_number = extract_longest_number(annotation_descriptions)

        i = list_of_file_names.index(name)

        return render_template(
            "image_page.html",
            name=name,
            image_file=f"/images/{name}.png",
            annotations=annotation_descriptions,
            prev=list_of_file_names[i - 1],
            next=list_of_file_names[(i + 1) % len(list_of_file_names)],
            ean=longest_number if len(longest_number) == 13 else "",
            latitude=gps_info.get("GPSLatitude"),
            longitude=gps_info.get("GPSLongitude"),
            created_at=date_info.get("CreateDate"),
        )

    # Route to validate EAN-13 (automatic validation)
    @app.route("/validate_ean/<ean>")
    def validate_ean(ean: str):
        # Validate EAN-13
        if not ean or not check_ean13(ean):
            # Return a 400 Bad Request response if the EAN is invalid
            return jsonify({"message": "Invalid EAN-13"}), 400
        # Return a 200 OK response if the EAN is valid
        return jsonify({"message": "Valid EAN-13"}), 200

    # Route to check Open Food Facts (manual request on button click)
    @app.route("/check_off/<ean>")
    def check_off(ean: str):
        # Ensure the EAN-13 is valid before proceeding
        if not check_ean13(ean):
            return render_template("validation_result.html", error="Invalid EAN-13")

        # Check Open Food Facts
        response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{ean}.json")
        if response.status_code == 200:
            product_data = response.json()
            if product_data.get("status") == 1:
                return render_template("validation_result.html", product=product_data.get("product"))
            return render_template("validation_result.html", error="Product not found in Open Food Facts")
        return render_template("validation_result.html", error="Error fetching data from Open Food Facts")

    return app


if __name__ == "__main__":
    # Create a list of image names (without extension)
    list_of_file_names = sorted([p.stem for p in BASE_IMAGE_DIR.glob("*.png") if p.with_suffix(".json").exists()])

    app = create_app(list_of_file_names)
    app.run(debug=True)
