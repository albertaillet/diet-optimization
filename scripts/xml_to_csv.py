"""This script takes an XML file as input and converts it to a CSV file and saves it to the provided path
NOTE: Currently this script just removes the < characters if they are part of the text due to (recover=True)

Usage of script python xml_to_csv.py input.xml output.csv
"""

import csv
import sys
from pathlib import Path

from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]


def main(input_file: Path, output_file: Path):
    parser = etree.XMLParser(encoding="windows-1252", recover=True)
    with input_file.open("rb") as f:
        root = etree.parse(f, parser).getroot()
    with output_file.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=[c.tag for c in root[0]])
        writer.writeheader()
        for xml_row in root:
            writer.writerow({c.tag: c.text.strip() if isinstance(c.text, str) else c.text for c in xml_row})


if __name__ == "__main__":
    if len(sys.argv) != 3:
        exit("Usage: python xml_to_csv.py input.xml output.csv")

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        exit(f"Input file {input_file} does not exist")
    if input_file.suffix != ".xml":
        exit(f"Input file {input_file} is not an XML file")

    output_file = Path(sys.argv[2])
    if not output_file.parent.exists():
        exit(f"Output directory {output_file.parent} does not exist")
    if output_file.suffix != ".csv":
        exit(f"Output file {output_file} is not a CSV file")

    main(input_file, output_file)
    print(f"Conversion successful. CSV file saved to {output_file}")
