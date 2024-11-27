#!/usr/bin/python3
"""Script to generate missing or corrupted Google Cloud Vision JSON.

To run, simply run as 'off' user, with the Google API_KEY as envvar:
`CLOUD_VISION_API_KEY='{KEY}' python3 run_ocr.py`

Missing JSON will be added, and corrupted JSON or Google Cloud Vision JSON
containing an 'errors' fields will be replaced.

Script taken and modified from:
https://github.com/openfoodfacts/openfoodfacts-server/blob/main/scripts/run_ocr.py
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import certifi
import requests

# Configuration
API_KEY = os.getenv("CLOUD_VISION_API_KEY")
if not API_KEY:
    sys.exit("missing Google Cloud CLOUD_VISION_API_KEY as envvar")

DATA_DIR = Path(os.getenv("DATA_DIR", ""))
BASE_IMAGE_DIR = DATA_DIR / "exported_images"
CLOUD_VISION_URL = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"


def get_base64_image_from_path(image_path: Path) -> str:
    """Read image file and convert to base64 string."""
    with image_path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def run_ocr_on_image_batch(base64_images: list[str], session: requests.Session) -> requests.Response:
    """Send batch of images to Google Cloud Vision API."""
    return session.post(
        CLOUD_VISION_URL,
        json={
            "requests": [
                {
                    "features": [
                        {"type": "TEXT_DETECTION"},
                        # {"type": "LOGO_DETECTION"},
                        # {"type": "LABEL_DETECTION"},
                        # {"type": "SAFE_SEARCH_DETECTION"},
                        # {"type": "FACE_DETECTION"},
                    ],
                    "image": {"content": base64_image},
                }
                for base64_image in base64_images
            ]
        },
    )


def run_ocr_on_image_paths(image_paths: list[Path], session: requests.Session, override: bool = False):
    """Process a batch of image paths through OCR."""
    images_content = []
    for image_path in image_paths:
        json_path = image_path.with_suffix(".json")
        if json_path.is_file() and not override:
            continue

        if json_path.is_file() and override:
            print(f"Deleting file {json_path}")
            json_path.unlink()

        content = get_base64_image_from_path(image_path)
        if content:
            images_content.append((image_path, content))

    if not images_content:
        return [], False

    r = run_ocr_on_image_batch([x[1] for x in images_content], session)
    r_json = r.json()

    if not r.ok:
        print(r_json)
        print(image_paths)
        return [], True

    responses = r_json["responses"]
    return [(images_content[i][0], responses[i]) for i in range(len(images_content))], True


def run_ocr(data_definition: Path, session: requests.Session, sleep: float = 0.0, override: bool = False):
    """Run OCR on images listed in data definition file."""
    print(f"Running OCR on {data_definition}")

    with data_definition.open("r") as f:
        image_paths = [data_definition.parent / f"{line.strip()}.png" for line in f]

    for path in image_paths:
        responses, performed_request = run_ocr_on_image_paths([path], session, override)

        for image_path, response in responses:
            json_path = image_path.with_suffix(".json")
            with json_path.open("w") as f:
                print(f"Dumping OCR JSON to {json_path}")
                json.dump({"responses": [response]}, f, indent=2)

        if performed_request and sleep:
            time.sleep(sleep)


if __name__ == "__main__":
    print(f"{API_KEY=}")
    parser = argparse.ArgumentParser()
    parser.add_argument("--override", action="store_true", help="Override existing JSON files")
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep time between requests")
    args = parser.parse_args()

    # Initialize session with certificate verification
    session = requests.Session()
    requests.get("https://vision.googleapis.com", verify=certifi.where())

    data_definition = DATA_DIR / "exported_images/data.txt"
    if not data_definition.is_file():
        sys.exit(f"Data definition file not found: {data_definition}")

    run_ocr(data_definition, session, sleep=args.sleep, override=args.override)
