import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from PIL import Image


def image_info(image_path: Path):
    image = Image.open(image_path)

    # Decode the XMP data
    xmp_data = image.info["xmp"].decode("utf-8")

    # Parse the XML
    root = ET.fromstring(xmp_data)

    gps_info = {}
    date_info = {}

    # Extract GPS information
    for elem in root.iter("{http://ns.adobe.com/exif/1.0/}GPSLatitude"):
        gps_info["GPSLatitude"] = elem.text

    for elem in root.iter("{http://ns.adobe.com/exif/1.0/}GPSLongitude"):
        gps_info["GPSLongitude"] = elem.text

    # Extract date information
    for elem in root.iter("{http://ns.adobe.com/xap/1.0/}CreateDate"):
        date_info["CreateDate"] = elem.text

    for elem in root.iter("{http://ns.adobe.com/xap/1.0/}ModifyDate"):
        date_info["ModifyDate"] = elem.text

    return gps_info, date_info


def parse_lat_long(value: str) -> str:
    # Convert the latitude/longitude string to a float
    return value


def parse_date(value: str) -> datetime:
    # Convert the date string to a datetime object
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")


if __name__ == "__main__":
    # Print the extracted information
    gps_info, date_info = image_info(Path("data/exported_images/IMG_5911.png"))
    print("GPS Information:")
    for key, value in gps_info.items():
        print(f"{key}: {value} ({type(value)})")

    print("\nDate Information:")
    for key, value in date_info.items():
        print(f"{key}: {value} ({type(value)})")
