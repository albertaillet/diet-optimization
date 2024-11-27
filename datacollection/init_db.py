#!/usr/bin/env python3
"""Initialize the database with data from existing images."""

import os
import sqlite3
from pathlib import Path

from datacollection.database import Database, ImageData
from utils.image import image_info

# Get data directory from environment variable or use default
DATA_DIR = Path(os.getenv("DATA_DIR", "")).resolve()
BASE_IMAGE_DIR = DATA_DIR / "exported_images"
DB_PATH = DATA_DIR / "images.db"


def validate_db(db: Database, list_of_file_names: list[str]) -> tuple[set[str], set[str]]:
    """Validate database against filesystem."""
    # Get all image names from filesystem
    fs_images = set(list_of_file_names)

    # Get all image names from database
    db_images = set()
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image_name FROM images")
        db_images = {row[0] for row in cursor.fetchall()}

    # Find differences
    missing_in_db = fs_images - db_images
    missing_in_fs = db_images - fs_images

    if missing_in_db:
        print(f"Found {len(missing_in_db)} images in filesystem that aren't in database: {missing_in_db}")
    if missing_in_fs:
        print(f"Found {len(missing_in_fs)} images in database that don't exist on filesystem: {missing_in_fs}")
    return missing_in_db, missing_in_fs


def init_db():
    """Initialize database with data from existing images."""
    list_of_file_names = sorted([p.stem for p in BASE_IMAGE_DIR.glob("*.png")])
    print(f"Found {len(list_of_file_names)} images in filesystem")

    db = Database(DB_PATH)
    if DB_PATH.exists():
        missing_in_db, missing_in_fs = validate_db(db, list_of_file_names)

        if missing_in_fs:
            print(f"Warning: Found {len(missing_in_fs)} entries in database with no image files:")
            for name in sorted(missing_in_fs):
                print(f"  - {name}")
        if not missing_in_db:
            print("Database is up to date!")
            return
        print(f"Processing {len(missing_in_db)} new images:")

    # Process each image
    for name in list_of_file_names:
        print(f"Processing {name}")

        # Get GPS and date info from image
        gps_info, date_info = image_info(DATA_DIR / f"{name}.png")

        # Create ImageData object
        image_data = ImageData(
            image_name=name,
            ean=None,  # EAN will be added later through the web interface
            latitude=gps_info.get("GPSLatitude"),
            longitude=gps_info.get("GPSLongitude"),
            created_at=date_info.get("CreateDate"),
            last_updated=None,  # This will be set automatically by SQLite
        )

        # Insert into database
        db.insert_image_data(image_data)

    print("Database initialization complete")


if __name__ == "__main__":
    init_db()
