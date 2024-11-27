import sqlite3
from pathlib import Path
from typing import NamedTuple


class ImageData(NamedTuple):
    image_name: str
    ean: str | None
    latitude: float | None
    longitude: float | None
    created_at: str | None
    last_updated: str | None


class Database:
    def __init__(self, db_path: Path):
        """Initialize the database with required tables."""
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    image_name TEXT PRIMARY KEY NOT NULL,
                    ean TEXT,
                    latitude REAL,
                    longitude REAL,
                    created_at TEXT,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def insert_image_data(self, image_data: ImageData) -> None:
        """Insert or update image data in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO images (image_name, ean, latitude, longitude, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(image_name) DO UPDATE SET
                    ean = COALESCE(excluded.ean, ean),
                    latitude = COALESCE(excluded.latitude, latitude),
                    longitude = COALESCE(excluded.longitude, longitude),
                    created_at = COALESCE(excluded.created_at, created_at),
                    last_updated = CURRENT_TIMESTAMP
            """,
                (
                    image_data.image_name,
                    image_data.ean,
                    image_data.latitude,
                    image_data.longitude,
                    image_data.created_at,
                ),
            )
            conn.commit()

    def get_image_data(self, image_name: str) -> ImageData | None:
        """Retrieve image data from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT image_name, ean, latitude, longitude, created_at, last_updated
                FROM images WHERE image_name = ?
            """,
                (image_name,),
            )
            row = cursor.fetchone()
            return ImageData(*row) if row else None

    def update_ean(self, image_name: str, ean: str) -> None:
        """Update the EAN for a specific image."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE images
                SET ean = ?, last_updated = CURRENT_TIMESTAMP
                WHERE image_name = ?
            """,
                (ean, image_name),
            )
            conn.commit()
