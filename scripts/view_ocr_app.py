import json
import os
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, send_from_directory

DATA_DIR = Path(os.getenv("DATA_DIR", "")).resolve()
BASE_IMAGE_DIR = DATA_DIR / "exported_images"

# TODO: Use this together with a regex to extract a proposed barcode.
# def check_ean13(number: int) -> bool:
#     """Based on https://en.wikipedia.org/wiki/International_Article_Number#Position_%E2%80%93_weight."""
#     num_str = str(number)
#     assert len(num_str) == 13, f"{number} is not 13 digits long."
#     remainder = sum(int(num_str[i]) * (3 if i % 2 else 1) for i in range(12)) % 10
#     check_digit = 10 - remainder if remainder else 0
#     return int(num_str[-1]) == check_digit


def create_app(list_of_file_names: list[str]) -> Flask:
    app = Flask(__name__)

    # Route for the main page with links to each image
    @app.route("/")
    def index():
        return render_template("index.html", names=list_of_file_names)

    # Route to serve static images
    @app.route("/images/<path:image_filename>")
    def serve_image(image_filename):
        return send_from_directory(BASE_IMAGE_DIR, image_filename)

    # Dynamic route for each image based on the file name
    @app.route("/<name>")
    def image_page(name):
        image_file = BASE_IMAGE_DIR / f"{name}.png"
        annotation_file = BASE_IMAGE_DIR / f"{name}.json"

        if not image_file.exists() or not annotation_file.exists():
            abort(404)

        with annotation_file.open("r") as f:
            data = json.load(f)

        responses = data.get("responses", [])
        if len(responses) != 1:
            return jsonify({"error": "Invalid response length"}), 400

        annotations = responses[0].get("textAnnotations", [])
        annotation_descriptions = [ann["description"] for ann in annotations]

        return render_template(
            "image_page.html",
            name=name,
            image_file=f"/images/{name}.png",
            annotations=annotation_descriptions,
            names=list_of_file_names,
        )

    return app


if __name__ == "__main__":
    # Create a list of image names (without extension)
    list_of_file_names = sorted([p.stem for p in BASE_IMAGE_DIR.glob("*.png") if p.with_suffix(".json").exists()])

    app = create_app(list_of_file_names)
    app.run(debug=True)
